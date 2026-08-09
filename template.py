# -*- coding: utf-8 -*-
# ============================================================
# FongMi / RanXin TV 通用 Python spider 模板
# 用法: 复制本文件改名字，改 class Spider 里的实现，托管到 http(s)，
#       订阅 JSON 里加 {"key":"xx","name":"xx","api":"你的url.py","type":3}
# ============================================================
# ★ 核心：你只需要实现下面这些方法，返回固定格式的 JSON（字符串）即可。
#   Spider 不存视频，只负责"抓数据→转成播放器能认的格式"。
# ============================================================
import json
import requests
from lxml import etree


class Spider:
    # ---------------- 配置区 ----------------
    # 采集站 macCMS 风格接口: 形如 http://xxx/api.php/provide/vod/
    api = "http://你的域名/api.php/provide/vod/"
    headers = {"User-Agent": "Mozilla/5.0"}
    timeout = 15

    # ---------------- 0. 初始化 ----------------
    # extend 是站点配置里传入的额外参数（可用来动态传域名/token）
    def init(self, extend=""):
        if extend:
            parts = str(extend).split("|")
            if parts[0]:
                self.api = parts[0].strip()

    # ---------------- 1. 首页分类 ----------------
    # 返回: {"class":[{type_id,type_name},...], "list":[视频...]}
    def homeContent(self, filter):
        classes = [
            {"type_id": "电影", "type_name": "电影"},
            {"type_id": "电视剧", "type_name": "电视剧"},
            {"type_id": "综艺", "type_name": "综艺"},
            {"type_id": "动漫", "type_name": "动漫"},
        ]
        return {"class": classes, "list": []}

    # ---------------- 2. 分类点播列表 ----------------
    # tid=分类id, pg=页码
    # 返回: {"list":[视频...], "page":1, "pagecount":N, "limit":N, "total":N}
    def categoryContent(self, tid, pg, filter, extend):
        # 注意: macCMS 的 class 参数是"分类id"(数字或字母)，不是中文名
        url = self.api + "?ac=list&t=" + str(tid) + "&pg=" + str(pg)
        data = self._get_json(url)
        vlist = [self._fmt_vod(it) for it in data.get("list", [])]
        return {
            "list": vlist,
            "page": int(pg),
            "pagecount": int(data.get("pagecount") or 1),
            "limit": 20,
            "total": int(data.get("total") or 0),
        }

    # ---------------- 3. 详情(含播放源) ----------------
    # ids=["视频id"]
    # 返回: {"list":[{vod_id,vod_name,vod_pic,type_name,..vod_play_from,vod_play_url}]}
    def detailContent(self, ids):
        vid = ids[0] if isinstance(ids, list) else ids
        url = self.api + "?ac=detail&ids=" + str(vid)
        data = self._get_json(url)
        it = (data.get("list") or [{}])[0]
        vod = {
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
            # 多线路: 线路名用 $$$ 分隔
            "vod_play_from": it.get("vod_play_from", ""),
            # 每个线路内: 集数用 # 分隔, 每集 "集名$播放地址"
            # 例: "第1集$http://a.m3u8#第2集$http://b.m3u8$$$第1集$http://c.mp4"
            "vod_play_url": it.get("vod_play_url", ""),
        }
        return {"list": [vod]}

    # ---------------- 4. 搜索 ----------------
    # key=关键字
    def searchContent(self, key, quick, pg="1"):
        url = self.api + "?ac=detail&wd=" + str(key) + "&pg=" + str(pg)
        data = self._get_json(url)
        return {"list": [self._fmt_vod(it) for it in data.get("list", [])]}

    # ---------------- 5. 播放 ----------------
    # flag=线路名, id=该集播放地址(vod_play_url里的url)
    # 返回直链直接播; 若是网页需走解析接口, parse=1 并给 playUrl
    def playerContent(self, flag, id, vipFlags):
        low = str(id).lower()
        direct = any(x in low for x in (".m3u8", ".mp4", ".flv", ".mkv", ".ts",
                                        ".rmvb", ".avi", ".webm"))
        if direct:
            return {"parse": 0, "playUrl": "", "url": id}
        # 网页源 → 走通用解析接口(换成你的解析接口, 留空则用 app 内置)
        return {"parse": 1, "playUrl": "", "url": id}

    # ================ 工具方法(自己加的, 不要求) ================
    def _get_json(self, url):
        r = requests.get(url, headers=self.headers, timeout=self.timeout)
        return r.json()

    # 列表页每条视频的字段转换（列表只给基础信息, 不给播放源）
    def _fmt_vod(self, it):
        return {
            "vod_id": str(it.get("vod_id", "")),
            "vod_name": it.get("vod_name", ""),
            "vod_pic": it.get("vod_pic", ""),
            "type_name": it.get("type_name", ""),
            "vod_remarks": it.get("vod_remarks", ""),
        }


# ============================================================
# 另一种常见数据源: 普通 HTML 网页 + XPath 抓取
# （很多片源站没有 API, 只有网页, 就用这种方式）
# 用法: class Spider 换成下面这种, 或把方法拷过去改
# ============================================================
class HtmlSpider(Spider):
    # 例: 一个带分类的站, 页面结构类似:
    #   <ul><li><a href="/vod/1.html">片名</a><img src="poster.jpg"></li></ul>
    list_url = "http://xxx.com/list/{tid}-{pg}.html"
    detail_url = "http://xxx.com/vod/{id}.html"

    def categoryContent(self, tid, pg, filter, extend):
        url = self.list_url.format(tid=tid, pg=pg)
        r = requests.get(url, headers=self.headers, timeout=self.timeout)
        tree = etree.HTML(r.text)          # 解析 HTML
        vlist = []
        for a in tree.xpath('//ul/li/a'):
            href = a.get("href")                       # 详情页地址
            name = a.xpath("string(.)").strip()        # 片名
            img = a.xpath("./preceding-sibling::img[1]/@src")
            vid = href.rstrip(".html").split("/")[-1] if href else ""
            vlist.append({
                "vod_id": vid,
                "vod_name": name,
                "vod_pic": img[0] if img else "",
                "type_name": "",
            })
        # 分页: 一般从"下一页"链接或页码数字推断
        return {"list": vlist, "page": int(pg), "pagecount": 20,
                "limit": len(vlist), "total": 0}

    def detailContent(self, ids):
        vid = ids[0] if isinstance(ids, list) else ids
        r = requests.get(self.detail_url.format(id=vid), headers=self.headers,
                         timeout=self.timeout)
        tree = etree.HTML(r.text)
        # 播放列表一般是: 线路->集数按钮->播放地址(iframe/script/接口)
        # 例: <div class="play"><a href="播放链接">第1集</a>...
        eps = []
        for a in tree.xpath('//div[contains(@class,"play")]//a'):
            eps.append("%s$%s" % (a.xpath("string(.)").strip(), a.get("href")))
        return {"list": [{
            "vod_id": vid,
            "vod_name": tree.xpath("string(//h1)").strip(),
            "vod_pic": "",
            "vod_content": tree.xpath("string(//*[contains(@class,'intro')])").strip(),
            "vod_play_from": "默认线路",
            "vod_play_url": "#".join(eps),
        }]}

    # HTML 网页抓取的核心难点: 播放地址往往藏在 iframe 或 ajax 接口里,
    # 需要: 1) 抓 iframe src 2) 找 ajax 接口 3) 用正则/接口拿真实 m3u8
    def playerContent(self, flag, id, vipFlags):
        # 网页播放页 → 抓页面里的真实流地址
        r = requests.get(id, headers=self.headers, timeout=self.timeout)
        import re
        m = re.search(r"(https?://[^\"']+?\.(?:m3u8|mp4)[^\"']*)", r.text)
        if m:
            return {"parse": 0, "playUrl": "", "url": m.group(1)}
        return {"parse": 1, "playUrl": "", "url": id}
