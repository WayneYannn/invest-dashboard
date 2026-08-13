# idc-dash

内部数据看板。

## 本地预览

```bash
python3 -m http.server 8000
# 浏览器打开 http://localhost:8000/
```

> 直接双击 index.html 无法读取 data/，请用本地服务器或部署后的网址打开。

## 维护

阈值与规则在 `index.html` 的 JS 中。改完推送后手动触发部署即可生效。
