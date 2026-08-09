# -*- coding: utf-8 -*-
# ============================================================
# 360zy 采集站 spider — 适配 FongMi TV / OK影视 Python 引擎
# 接口: MacCMS 标准 https://360zy.com/api.php/provide/vod/
# ============================================================
import json
import requests

api = "https://360zy.com/api.php/provide/vod/"


def get(url):
    return requests.get(url, headers={"User-Agent": "Mozilla/5.0"},
                        timeout=15).json()


def fmt(it):
    return {
        "vod_id": str(it.get("vod_id", "")),
        "vod_name": it.get("vod_name", ""),
        "vod_pic": it.get("vod_pic", ""),
        "type_name": it.get("type_name", ""),
        "vod_remarks": it.get("vod_remarks", ""),
    }


class Spider:
    def init(self, extend=""):
        pass

    # 首页分类：拉 ?ac=list 里的 class 字段
    def homeContent(self, filter):
        try:
            data = get(api + "?ac=list&pg=1")
            classes = [{"type_id": str(c["type_id"]), "type_name": c["type_name"]}
                       for c in (data.get("class") or [])]
        except Exception:
            classes = [{"type_id": "1", "type_name": "电影"},
                       {"type_id": "2", "type_name": "连续剧"},
                       {"type_id": "3", "type_name": "综艺"},
                       {"type_id": "4", "type_name": "动漫"}]
        return {"class": classes, "list": []}

    # 分类列表
    # 注意: 360zy 服务端不支持 t= 分类过滤(返回空/全量)，这里客户端按 type_id 过滤
    def categoryContent(self, tid, pg, filter, extend):
        try:
            data = get(api + "?ac=list&pg=%s" % pg)
            vlist = [fmt(it) for it in (data.get("list") or [])
                     if str(it.get("type_id")) == str(tid)]
            return {"list": vlist,
                    "page": int(data.get("page") or pg),
                    "pagecount": int(data.get("pagecount") or 1),
                    "limit": len(vlist) or 1,
                    "total": int(data.get("total") or 0)}
        except Exception as e:
            return {"list": [], "page": int(pg), "pagecount": 1,
                    "limit": 1, "total": 0, "error": str(e)}

    # 详情 + 播放源
    def detailContent(self, ids):
        vid = ids[0] if isinstance(ids, list) else ids
        try:
            data = get(api + "?ac=detail&ids=%s" % vid)
            it = (data.get("list") or [{}])[0]
            # 播放源: vod_play_from(线路名,$$$分隔) + vod_play_url(集数)
            return {"list": [{
                "vod_id": str(it.get("vod_id", vid)),
                "vod_name": it.get("vod_name", ""),
                "vod_pic": it.get("vod_pic", ""),
                "type_name": it.get("type_name", ""),
                "vod_year": it.get("vod_year", ""),
                "vod_area": it.get("vod_area", ""),
                "vod_actor": it.get("vod_actor", ""),
                "vod_director": it.get("vod_director", ""),
                "vod_remarks": it.get("vod_remarks", ""),
                "vod_content": it.get("vod_content", ""),
                "vod_play_from": it.get("vod_play_from", "360zy"),
                "vod_play_url": it.get("vod_play_url", ""),
            }]}
        except Exception as e:
            return {"list": [{"vod_id": vid, "vod_name": "解析失败",
                              "error": str(e)}]}

    # 搜索
    def searchContent(self, key, quick, pg="1"):
        try:
            data = get(api + "?ac=videolist&wd=%s&pg=%s" % (key, pg))
            return {"list": [fmt(it) for it in (data.get("list") or [])]}
        except Exception as e:
            return {"list": [], "error": str(e)}

    # 播放：MacCMS 返回的 vod_play_url 就是直链
    def playerContent(self, flag, id, vipFlags):
        return {"parse": 0, "playUrl": "", "url": id}
