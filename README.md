# tvbox_osc — TVBox/FongMi 自用配置

## 文件说明

| 文件 | 用途 |
|---|---|
| **360zy.json** | FongMi/TVBox 订阅配置，360zy 采集站（1080p，无门槛，当天更新）。填 jsDelivr 地址即用 |
| **shenma_vod.py** | 神马TV(新趣看4K) 点播 spider，协议逆向自 APK。需替换有效 api/token 才能出内容 |
| **template.py** | FongMi Python spider 通用模板（JSON API + XPath 两种写法） |

## 订阅地址

```
https://cdn.jsdelivr.net/gh/samuelamg/tvbox_osc@main/360zy.json
```

## 用法

1. FongMi TV / TVBox / OK影视 → 设置 → 订阅/接口 → 添加订阅
2. 粘贴上面 jsDelivr 地址
3. 拉取后即可使用 360zy 采集站

## 备注

- 360zy 是采集站直链源，画质 1080p 封顶；真 4K 需网盘源（小雅/夸克）
- spider 文件（.py）需另行托管并通过站点 api 字段引用
