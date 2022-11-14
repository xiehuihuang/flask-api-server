#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @file: mixin.py
# @time: 2020/9/15 16:14
# @author: jack
# @Email: 793936517@qq.com
# @desc:
import collections
import logging
import re

from flask import request
from sqlalchemy import text, cast

from decimal import Decimal
from main.setting import db
from main.util.common import json_resp
from main.util.error import PlusException
from main.util.response_code import RET

logger = logging.getLogger(__name__)


class RawQueryHandle:
    @staticmethod
    def raw_params_to_filter(params):
        re_escape = re.compile(r"([\\'])")
        return " and ".join([f"{k}='" + re_escape.sub(r'\\\1', v) + "'" for k, v in params.items()]) or "1=1"

    @staticmethod
    def raw_get_sql_count(sql):
        query = db.session.execute(sql)
        return query.rowcount()

    @staticmethod
    def raw_get_sql_keys(sql):
        query = db.session.execute(sql)
        return query.keys()

    @staticmethod
    def raw_queryset_to_dict(queryset, default=None):
        if not queryset:
            return {}
        row = queryset.items()
        return {x[0]: x[1] if x[1] is not None else default for x in row}

    @classmethod
    def raw_queryset_list_to_dict_list(cls, queryset, default=None):
        return [cls.raw_queryset_to_dict(x, default) for x in queryset]

    @staticmethod
    def raw_get_sql_fetchone(sql, must=True, default=None):
        query = db.session.execute(text(sql))
        queryset = query.fetchone()
        if not queryset:
            if must:
                return {x: default for x in query.keys()}
            return {}
        row = queryset.items()
        return {x[0]: x[1] if x[1] is not None else default for x in row}

    @staticmethod
    def raw_get_sql_fetchall(sql, default=None):
        queryset = db.session.execute(text(sql)).fetchall()
        ret = []
        for row in queryset:
            content = row.items()
            ret.append({x[0]: x[1] if x[1] is not None else default for x in content})
        return ret


class BaseViewMixin:
    like_field = []

    @property
    def queryset(self):
        return self.model.query.filter_by(is_deleted=0)

    def perform_query(self, queryset, params):
        like_field = self.like_field
        return queryset.filter_by(**{x: params[x] for x in params if x not in like_field}).filter(
            *[cast(getattr(self.model, x), db.String).like(f"%{params[x]}%") for x in params
              if hasattr(self.model, x) and x in like_field])

    def post_query(self):
        self.resources += "查询"
        logger.info(f"{self.resources} user:{self.current_user.username} params:{self.request_data}")
        params = {x: self.request_data.get(x) for x in self.query_field if self.request_data.get(x, "") != ""}

        queryset = self.perform_query(self.queryset, params)
        queryset = queryset.order_by(self.model.id.desc())
        offset = self.request_data.get("offset")
        limit = self.request_data.get("limit")
        if offset and limit:
            instance = queryset.offset((int(offset) - 1) * int(limit)).limit(int(limit)).all()
            total = queryset.count()
        else:
            instance = queryset.all()
            total = len(instance)

        data = self.model.to_list(instance)
        return json_resp(RET.OK, f"{self.resources}成功", data=data, total=total)

    def create(self):
        self.resources += "创建"
        logger.info(f"{self.resources} user:{self.current_user.username} params:{self.request_data}")
        params = {x: self.request_data.get(x) for x in self.create_field if self.request_data.get(x) is not None}

        if not all([x in params for x in self.create_required_field]):
            raise PlusException(f"缺少必填参数")

        params["author"] = self.current_user.username
        obj = self.model(**params)
        data = obj.create()

        return json_resp(RET.OK, f"{self.resources}成功", data=data)

    @property
    def update_queryset(self):
        return self.model.query.filter_by(is_deleted=0)

    def update(self):
        self.resources += "更新"
        logger.info(f"{self.resources} user:{self.current_user.username} params:{self.request_data}")
        params = {x: self.request_data.get(x) for x in self.update_field if self.request_data.get(x) is not None}

        if not all([x in params for x in self.update_required_field]):
            raise PlusException("缺少必填参数")
        pk = params.pop("id")

        params["author"] = self.current_user.username
        result = self.update_queryset.filter_by(id=pk).update(params)
        self.db_commit()

        return json_resp(RET.OK, f"{self.resources}成功", data=result)

    @property
    def delete_queryset(self):
        return self.model.query.filter_by(is_deleted=0)

    def abs_delete(self):
        self.resources += "物理删除"
        logger.info(f"{self.resources} user:{self.current_user.username} params:{self.request_data}")

        pk = self.request_data.get("id")
        if pk is None:
            raise PlusException("缺少id参数")

        result = self.delete_queryset.filter_by(id=pk).delete()
        self.db_commit()

        return json_resp(RET.OK, f"{self.resources}成功", data=result)


class GraphicsDataHandle:
    """
    图表数据处理
    """
    @staticmethod
    def get_city_select_list(table, key1, key2):
        queryset = db.session.query(
            getattr(table.columns, key1),
            getattr(table.columns, key2),
        ).all()
        return GraphicsDataHandle.get_select_list(queryset)

    @staticmethod
    def get_select_list(queryset):
        data = {}
        for i in queryset:
            father = i[0]
            son = i[1]
            if father not in data:
                data[father] = []
            if son in data[father]:
                continue
            data[father].append(son)
        return data

    @staticmethod
    def get_norm_options(queryset):
        data = {}
        for row in queryset:
            father = row[0]
            son = row[1]
            if father not in data:
                data[father] = []
            if son in data[father]:
                continue
            data[father].append(son)
        ret = []
        for f in data:
            childs = []
            for s in data[f]:
                childs.append({"name": s, "pName": f})
            ret.append({"name": f, "childs": childs})
        return ret

    @staticmethod
    def queryset_to_horizontal(name, queryset, reverse=False):
        """
        条形图
        """
        ret = {
            "viewName": name,
            "columns": [],
            "rows": [],
        }
        if reverse:
            queryset = queryset[::-1]

        for i in queryset:
            if i[0] is None or i[1] is None:
                continue
            ret["columns"].append(i[0])
            ret["rows"].append(i[1])
        return ret

    @staticmethod
    def queryset_to_line(name, queryset, start_index=0, rule=None, graph_type="line"):
        """
        多线图
        组内柱状图
        {
                "chartType":"line",
                "columns":[
                    "09-05"
                ],
                "legend":[
                    "华南",
                    "华北",
                    "中东",
                    "华西",
                    "全国"
                ],
                "rows0":[
                    15
                ],
                "rows1":[
                    15
                ],
                "rows2":[
                    15
                ],
                "rows3":[
                    15
                ],
                "rows4":[
                    15
                ],
                "viewName":"各大区非运营里程违规情况（近30天）",
                "year":[

                ]
        }
        """
        ret = {
            "viewName": name,
            "year": [],
            "chartType": graph_type,
            "legend": [],
            "columns": [],
            "rows0": [],
        }
        temp_date = {}
        for i in queryset:
            if i[0] not in temp_date:
                temp_date[i[0]] = {"date": [], "value": [], }
            temp_date[i[0]]["date"].append(i[1])
            temp_date[i[0]]["value"].append(i[2])

        if rule:
            sort_key = sorted(temp_date, key=lambda x: rule.get(x, 1000))
            temp_date = {x: temp_date[x] for x in sort_key}

        for index, k in enumerate(temp_date):
            ret["legend"].append(k)
            ret["columns"] = temp_date[k]["date"]
            ret["rows" + str(index + start_index)] = temp_date[k]["value"]
        return ret

    @staticmethod
    def queryset_to_group_pillar(name, queryset):
        """
        组内柱状图
        """
        ret = {
            "viewName": name,
            "year": [],
            "chartType": "bar",
            "legend": [],
            "columns": [],
            "rows0": [],
        }
        for index, column in enumerate(queryset):
            if index == 0:
                ret["columns"] = column
            else:
                if index % 2:
                    ret["legend"].append(column[0])
                else:
                    ret["rows" + str(index // 2 - 1)] = column
        return ret

    @staticmethod
    def queryset_to_pillar_line(name, legend, queryset, graph_type=None):
        """
        组内柱状图和线
        {
            "columns": [
                "09-01",
                "09-02",
                "09-03",
                "09-04",
                "09-05"
                ],
            "legend": [
                "违规数量",
                "单车日均里程"
                ],
            "rows": [
                {
                    "data": [
                        15,
                        15,
                        15,
                        15,
                        15
                        ],
                    "name": "违规数量"
                    },
                {
                    "data": [
                        11.1,
                        11.1,
                        11.1,
                        11.1,
                        11.1
                        ],
                    "name": "单车日均里程"
                    }
                ],
            "viewName": "各城市非运营里程违规情况（近30天）",
            "year": []
            }
        """
        ret = {
            "viewName": name,
            "legend": legend,
            "rows": [],
            "columns": []
        }
        for index, name in enumerate(legend):
            ret["rows"].append({"name": name, "data": [],
                                "type": graph_type[index] if graph_type and len(graph_type) > index else "bar"})

        for i in queryset:
            ret["columns"].append(i[0])
            for index, rows in enumerate(ret["rows"]):
                rows["data"].append(i[index + 1])
        return ret

    @staticmethod
    def queryset_to_more_pie(name, queryset):
        """
        内外圈饼图
        """
        ret = {
            "viewName": name,
            "insideRows": [],
            "outRows": [],
        }
        large = collections.OrderedDict()
        small = collections.OrderedDict()
        for i in queryset:
            if i[0] not in large:
                large[i[0]] = i[2]
            else:
                large[i[0]] += i[2]
            if i[1] not in small:
                small[i[1]] = i[2]
            else:
                small[i[1]] += i[2]

        for k, v in large.items():
            ret["insideRows"].append({"name": k, "value": v})

        for k, v in small.items():
            ret["outRows"].append({"name": k, "value": v})
        return ret

    @staticmethod
    def queryset_to_left_right(name, queryset, legend=(), sum_field="", rule=None):
        """
        单柱状加线图
        """
        ret = {
            "viewName": name,
            "year": [],
            "legend": legend,
            "columns": [],
            "rows": [],
            "rowsRate": [],
        }

        if rule:
            queryset = sorted(queryset, key=lambda x: rule.get(x[0], 1000))

        for i in queryset:
            ret["columns"].append(i[0])
            ret["rows"].append(i[1])
            ret["rowsRate"].append(i[2])

        if sum_field and ret["columns"]:
            ret["columns"].insert(0, sum_field)
            ret["rows"].insert(0, sum(ret["rows"]))
            ret["rowsRate"].insert(0, sum(ret["rowsRate"]))
        return ret

    @staticmethod
    def queryset_to_pillar(name, queryset, legend=(), sum_field="", rule=None):
        """
        柱状图
        """
        ret = {
            "viewName": name,
            "year": [],
            "legend": legend,
            "columns": [],
            "rows": [],
        }

        if rule:
            queryset = sorted(queryset, key=lambda x: rule.get(x[0], 1000))

        for i in queryset:
            ret["columns"].append(i[0])
            ret["rows"].append(i[1])

        if sum_field and ret["columns"]:
            ret["columns"].insert(0, sum_field)
            ret["rows"].insert(0, sum(ret["rows"]))
        return ret

    @staticmethod
    def queryset_to_pie_chart(name, queryset, rule=None):
        """
        饼图
        """
        ret = {
            "viewName": name,
            "rows": [],
        }
        if rule:
            queryset = sorted(queryset, key=lambda x: rule.get(x[0], 1000))

        for i in queryset:
            ret["rows"].append({"name": i[0], "value": i[1]})
        return ret

    @staticmethod
    def queryset_to_table(name, queryset):
        """
        表格
        """
        ret = {
            "viewName": name,
            "thead": {
                "type": [],
                "columns": []
            },
            "rows": []
        }
        row_list = []
        if queryset:
            ret["thead"]["type"].extend([queryset[0][0], queryset[0][2]])
            ret["thead"]["columns"].extend(sorted(list(set([x[3] for x in queryset]))))
            row_list.extend(sorted(list(set([x[1] for x in queryset]))))
        for i in row_list:
            rows = [i]
            for j in ret["thead"]["columns"]:
                year_value = [x[4] for x in queryset if x[1] == i and x[3] == j]
                rows.append(year_value[0] if len(year_value) > 0 else '-')
            ret["rows"].append(rows)

        return ret

    @staticmethod
    def queryset_to_more_bar(name, queryset, rule=None):
        """
        多柱状图叠加
        """
        stack = []
        ret = {
            "viewName": name,
            "year": [],
            "stack": {
                "总计": stack
            },
            "columns": ['date'],
            "rows": [],
            "labelMap": {},
        }

        if rule:
            queryset = sorted(queryset, key=lambda x: rule.get(x[0], 1000))

        temp_date = {}
        for i in queryset:
            if i[0] not in temp_date.keys():
                count = 1
                temp_date[i[0]] = {"date": i[0]}

            if i[1] not in ret["labelMap"].values():
                ret["labelMap"]["item" + str(count)] = i[1]
                stack.append("item" + str(count))

            temp_date[i[0]]["item" + str(count)] = i[2]
            count += 1

        ret["columns"].extend(stack)
        for k, v in temp_date.items():
            ret["rows"].append(v)

        return ret

    @staticmethod
    def queryset_to_horizontal_data(name, queryset, rule=None, year=False):
        """
        条形图叠加
        """
        ret = {
            "viewName": name,
            "year": [],
            "legend": [],
            "columns": [],
            "rows": [],
        }

        if rule:
            queryset = sorted(queryset, key=lambda x: rule.get(x[0], 1000))

        for i in queryset:
            if i[0] not in ret["legend"]:
                ret["legend"].append(i[0])

            if i[1] not in ret["columns"]:
                ret["columns"].append(i[1])

        if year:
            ret["columns"] = sorted(ret["columns"], key=lambda x: int(x.strip("月")))

        if rule:
            ret["legend"] = sorted(ret["legend"], key=lambda x: rule.get(x, 1000))

        for i in ret["legend"]:
            rows = []
            for j in ret["columns"]:
                row = [x[2] for x in queryset if x[0] == i and x[1] == j]
                rows.extend(row if row else [0])

            ret["rows"].append(rows)
        return ret

    @staticmethod
    def queryset_to_ingredient(name, queryset_zip, sum_field="全国"):
        """
        瀑布成份图
        """
        ret = {
            "viewName": name,
            "xAxis": [],
            "barValArr": [],
            "surplusBarValArr": [],
        }
        if not queryset_zip:
            return ret

        sum_columns = sum(queryset_zip[1])
        ret["xAxis"] = [sum_field, *queryset_zip[0]]
        ret["barValArr"] = [sum_columns, *queryset_zip[1]]
        ret["surplusBarValArr"] = [0]

        for i in queryset_zip[1]:
            sum_columns -= i
            ret["surplusBarValArr"].append(sum_columns)

        return ret
