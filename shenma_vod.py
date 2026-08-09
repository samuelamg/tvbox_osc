# -*- coding: utf-8 -*-
# ============================================================
# 神马TV / 新趣看4K (com.qkysppkj.cc) 点播源 spider
# 协议逆向自 APK 静态代码，适配 FongMi / RanXin TV(BOX) 的 Python spider 接口
# ------------------------------------------------------------
# 接口协议（MacCMS 风格私有实现）:
#   列表:  {api}/api.php/{token}/vod/?ac=list&class={小写分类名}&page={n}&sort=Hotdesc
#   详情:  {api}/api.php/{token}/vod/{vod_id}      # vod_id 即列表项里的 nextlink
#   搜索:  POST {api}/api.php/{token}/SearchText
#   (替代搜索) {api}/api.php/{token}/vod/?ac=list&wd={关键字}
# 说明:
#   api/token 都是服务器下发的配置值（存于 app 的 SharedPreferences "initData"，RC4 加密），
#   APK 里写死的种子域名 www.smtvzm.com 已于 2026-08 失效(api.php 404)。
#   使用时把下面 api/token 改成你手里有效域名的对应值即可，改不了就用 init(extend) 传入。
# ============================================================
import json
import requests


class Spider:
    api = "http://www.smtvzm.com"   # Api_url：改成你设备/盒子里的真实域名
    token = ""                       # BASE_HOST：api.php 路径中的 token，来自服务器配置

    # 分类：class= 参数直接用"小写后的分类名"。下面为 app 内置分类，可按服务端实际分类增删
    classes = [
        {"type_id": "电影", "type_name": "电影"},
        {"type_id": "电视剧", "type_name": "电视剧"},
        {"type_id": "综艺", "type_name": "综艺"},
        {"type_id": "动漫", "type_name": "动漫"},
        {"type_id": "专题", "type_name": "专题"},
    ]

    SORT_HOT = "Hotdesc"   # 热度优先
    SORT_SCORE = "Scoredesc"  # 评分最高（未验证）
    SORT_TIME = "Timedesc"    # 最近更新（未验证）

    def init(self, extend=""):
        # extend 格式: "api" 或 "api|token"，如 "http://xxx.xxx|ABC123"
        if extend:
            parts = str(extend).split("|")
            if parts[0].strip():
                self.api = parts[0].strip().rstrip("/")
            if len(parts) > 1 and parts[1].strip():
                self.token = parts[1].strip()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 11) AppleWebKit/537.36",
            "Authorization": "",   # app 会带 RC4 解密的 Authorization，公开接口通常不需要
        }
        self.timeout = 15

    # ---------- 首页 ----------
    def homeContent(self, filter):
        return {"class": self.classes, "filters": {}, "list": []}

    def homeVideoContent(self):
        # 首页最近更新：取电影第一页
        return self.categoryContent("电影", "1", True, "")

    # ---------- 分类列表 ----------
    def categoryContent(self, tid, pg, filter, extend):
        try:
            url = ("%s/api.php/%s/vod/?ac=list&class=%s&page=%s&sort=%s"
                   % (self.api, self.token, str(tid).lower(), pg, self.SORT_HOT))
            r = requests.get(url, headers=self.headers, timeout=self.timeout)
            data = r.json()
            items = data.get("data") or []
            vlist = []
            for it in items:
                vlist.append({
                    "vod_id": str(it.get("nextlink") or ""),
                    "vod_name": it.get("title") or "",
                    "vod_pic": it.get("pic") or "",
                    "type_name": it.get("type") or "",
                    "vod_remarks": _remarks(it),
                    "vod_content": it.get("desc") or it.get("content") or it.get("intro") or "",
                })
            return {
                "list": vlist,
                "page": int(data.get("pageindex") or pg),
                "pagecount": int(data.get("totalpage") or 1),
                "limit": len(vlist) or 1,
                "total": int(data.get("videonum") or 0),
            }
        except Exception as e:
            return {"list": [], "page": int(pg), "pagecount": 1, "limit": 1, "total": 0,
                    "error": str(e)}

    # ---------- 详情 ----------
    def detailContent(self, ids):
        try:
            vid = ids[0] if isinstance(ids, list) else ids
            url = "%s/api.php/%s/vod/%s" % (self.api, self.token, vid)
            r = requests.get(url, headers=self.headers, timeout=self.timeout)
            d = r.json()

            play_from = []
            play_url = []
            for src in (d.get("video_list") or []):
                name = src.get("name") or "线路"
                eps = []
                for e in (src.get("list") or src.get("lists") or []):
                    et = e.get("title") or ""
                    eu = e.get("url") or ""
                    if et and eu:
                        eps.append("%s$%s" % (et, eu))
                if eps:
                    play_from.append(name)
                    play_url.append("#".join(eps))

            def _join(v):
                if isinstance(v, list):
                    return ",".join(str(x) for x in v if x)
                return str(v or "")

            vod = {
                "vod_id": vid,
                "vod_name": d.get("title") or "",
                "vod_pic": d.get("img_url") or "",
                "type_name": _join(d.get("type")),
                "vod_year": _year(d.get("pubtime")),
                "vod_area": _join(d.get("area")),
                "vod_actor": _join(d.get("actor")),
                "vod_director": _join(d.get("director")),
                "vod_remarks": _remarks(d),
                "vod_content": d.get("desc") or d.get("content") or d.get("intro") or "",
                "vod_play_from": "$$$".join(play_from),
                "vod_play_url": "$$$".join(play_url),
            }
            return {"list": [vod]}
        except Exception as e:
            return {"list": [{"vod_id": vid, "vod_name": "解析失败", "error": str(e)}]}

    # ---------- 搜索 ----------
    def searchContent(self, key, quick, pg="1"):
        try:
            # 主用 POST /SearchText（与 app 一致）
            url = "%s/api.php/%s/SearchText" % (self.api, self.token)
            r = requests.post(url, headers=self.headers, data={"wd": key},
                              timeout=self.timeout)
            try:
                data = r.json()
            except Exception:
                # 兜底：走 ac=list&wd
                url2 = "%s/api.php/%s/vod/?ac=list&wd=%s&page=%s" % (self.api, self.token, key, pg)
                data = requests.get(url2, headers=self.headers, timeout=self.timeout).json()
            items = data.get("data") or []
            return {"list": [_list_item(it) for it in items if it]}
        except Exception as e:
            return {"list": [], "error": str(e)}

    # ---------- 播放 ----------
    def playerContent(self, flag, id, vipFlags):
        # id 即 vod_play_url 里 "标题$url" 的 url 部分。直链(m3u8/mp4/flv)直接播，
        # 非直链源 app 靠自身 parse 解析，这里原样返回让播放器尝试。
        low = str(id).lower()
        direct = any(x in low for x in (".m3u8", ".mp4", ".flv", ".rmvb", ".avi",
                                        ".mkv", ".ts", ".webm", "m3u8:", "http"))
        return {"parse": 0 if direct else 1, "playUrl": "", "url": id}


def _remarks(it):
    st = it.get("state") or ""
    if it.get("is_finish"):
        return st or "已完结"
    return st


def _year(pub):
    if not pub:
        return ""
    s = str(pub)
    return s[:4] if len(s) >= 4 and s[:4].isdigit() else ""


def _list_item(it):
    return {
        "vod_id": str(it.get("nextlink") or ""),
        "vod_name": it.get("title") or "",
        "vod_pic": it.get("pic") or "",
        "type_name": it.get("type") or "",
        "vod_remarks": _remarks(it),
        "vod_content": it.get("desc") or it.get("content") or it.get("intro") or "",
    }
