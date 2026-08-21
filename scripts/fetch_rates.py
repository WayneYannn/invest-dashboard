#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
利率信号抓取脚本（多源冗余 + 失败回退）

抓取目标：
  - 10Y 国债收益率   (y10) → 新浪 bond 每日序列（已验证可用）
  -  `2Y 国债收益率   (y2)  → 新浪 bond 每日序列（已验证可用）
  -  1Y 国债收益率   (y1)  → 新浪 bond 每日序列（已验证可用，作为政策利率近似）
  -  CPI 同比        (cpi) → 国家统计局 CSV（待接入，当前回退手动）
  -  MLF 利率        (mlf) → 央行公告（待接入，当前用 y1 近似，见 note）

数据源策略：
  - 核心利率（10Y/2Y/1Y）用新浪，实测稳定、含历史序列、可做分位/趋势。
  - CPI/MLF 为非日频数据，找到稳定源后填入 SOURCES 即可自动；未接入时
    标记为 manual_required，看板手动补录，不阻塞整体运行。

输出：写入 data/auto.json 的 rates 字段。
"""
import urllib.request
import json
import datetime
import os
import sys

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.60',
    'Referer': 'https://stock.finance.sina.com.cn/',
}

TIMEOUT = 20


def fetch_json(url, headers=None):
    req = urllib.request.Request(url, headers=headers or HEADERS)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode('utf-8'))


def fetch_text(url, headers=None):
    req = urllib.request.Request(url, headers=headers or HEADERS)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read().decode('utf-8', errors='ignore')


# ---------- 新浪债券每日收益率序列（已验证） ----------
# 接口：https://bond.finance.sina.com.cn/hq/gb/daily?symbol=CN10YT
# 返回：{"code":0,"result":{"data":[{"d":"2026-08-20","o":..,"c":"1.683",..},..]}
# symbol 映射：CN10YT=10年, CN2YT=2年, CN1YT=1年, CN5YT=5年 ...
SINA_SYMBOL = {
    'y10': 'CN10YT',
    'y2':  'CN2YT',
    'y1':  'CN1YT',
}


def _sina_series(symbol):
    """取新浪某期限国债收益率的完整序列（最新1000交易日，含历史）。
    返回 (latest_val, latest_date, history_dict)，history_dict = {日期: 收益率%}"""
    url = f'https://bond.finance.sina.com.cn/hq/gb/daily?symbol={symbol}'
    d = fetch_json(url)
    rows = d.get('result', {}).get('data', [])
    if not rows:
        return None, None, {}
    last = rows[-1]
    latest_val = float(last['c'])
    latest_date = last['d']
    history = {}
    for r in rows:
        try:
            history[r['d']] = float(r['c'])
        except (ValueError, KeyError):
            continue
    return latest_val, latest_date, history


def src_sina_bond():
    """新浪债券：返回 {y10, y2, y1, history_10y, history_2y, history_1y, _src_dates}"""
    out = {}
    dates = {}
    histories = {}
    for key, sym in SINA_SYMBOL.items():
        val, dt, hist = _sina_series(sym)
        if val is not None:
            out[key] = val
            dates[key] = dt
            # 历史序列字段名映射：y10->history_10y, y1->history_1y, y2->history_2y
            hk = 'history_' + key[1:] + ('y' if not key.endswith('y') else '')
            histories[hk] = hist
    if not out:
        return None
    out['_src_dates'] = dates
    out.update(histories)
    return out


# ---------- CPI（国家统计局，待验证接入） ----------
def src_stats_cpi():
    """国家统计局 CPI 月度同比 CSV（占位，验证后启用）。
    参考：https://data.stats.gov.cn/ 或 公开镜像 CSV。"""
    raise NotImplementedError("CPI 源待接入")


# ---------- 多源清单：已验证的排前面 ----------
SOURCES = [
    ('sina_bond', src_sina_bond),
    # ('stats_cpi', src_stats_cpi),  # 接入后取消注释
]


def try_source(name, fn):
    try:
        sys.stderr.write(f'[INFO] 尝试数据源: {name}\n')
        r = fn()
        if r and any(k.startswith('y') and v is not None for k, v in r.items()):
            sys.stderr.write(f'[OK] 数据源 {name} 成功: {r}\n')
            return r
    except Exception as e:
        sys.stderr.write(f'[WARN] 数据源 {name} 失败: {e}\n')
    return None


def main():
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    out = {
        'updated_at': now.isoformat(),
        'source': 'manual_required',
        'y10': None, 'y2': None, 'y1': None, 'cpi': None, 'mlf': None,
        'src_dates': {},
        'note': '',
    }

    collected = {}
    src_name = 'manual_required'
    for name, fn in SOURCES:
        r = try_source(name, fn)
        if r:
            src_name = name
            for k, v in r.items():
                if k == '_src_dates':
                    out['src_dates'] = v
                elif v is not None:
                    collected[k] = v
            break  # 首个成功源即用（新浪已覆盖核心利率）

    out.update(collected)
    out['source'] = src_name

    # 未自动拿到的字段 → 标记手动
    missing = [k for k in ('y10', 'y2', 'y1', 'cpi', 'mlf') if out.get(k) is None]
    if missing:
        out['note'] = '以下字段需手动补录：' + ', '.join(missing)
        if 'cpi' in missing or 'mlf' in missing:
            out['note'] += '（CPI/MLF 为非日频，看板手动填或接入后自动）'
    else:
        out['note'] = '全部自动抓取成功'

    # 合并写入 auto.json
    base = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base, '..', 'data', 'auto.json')
    data = {}
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            data = {}
    data['rates'] = out
    with open(json_path, 'w',  encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    sys.stderr.write(f'[DONE] rates 写入完成: {out}\n')


if __name__ == '__main__':
    main()
