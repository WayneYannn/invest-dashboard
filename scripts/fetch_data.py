#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
投资看板 - 自动数据抓取脚本
抓取：基金最新净值（东方财富）、COMEX 黄金期货价（新浪）
输出：../data/auto.json
供 GitHub Actions 定时运行，结果随 GitHub Pages 自动发布。
"""
import urllib.request
import json
import datetime
import os
import sys

EM_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Referer': 'https://fundf10.eastmoney.com/',
}
SINA_HEADERS = {
    'User-Agent': 'Mozilla/5.0',
    'Referer': 'https://finance.sina.com.cn/',
}

# 看板覆盖的基金（代码 -> 名称）
FUNDS = {
    '400030': '东方添益债券',
    '007744': '长盛安逸纯债A',
    '018771': '汇添富稳合4个月D',
    '000218': '国泰黄金ETF联接A',
    '007467': '华泰柏瑞红利低波联接C',
}


def fetch_json(url, headers, timeout=15):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode('utf-8'))


def fetch_fund_nav(code):
    """东方财富历史净值接口，取最新一条。"""
    url = f'https://api.fund.eastmoney.com/f10/lsjz?fundCode={code}&pageIndex=1&pageSize=1'
    try:
        data = fetch_json(url, EM_HEADERS)
        lst = data.get('Data', {}).get('LSJZList', [])
        if not lst:
            return None
        r = lst[0]
        return {
            'code': code,
            'name': FUNDS.get(code, code),
            'nav': float(r['DWJZ']),
            'acc_nav': float(r['LJJZ']) if r.get('LJJZ') else None,
            'date': r['FSRQ'],
            'change_pct': float(r['JZZZL']) if r.get('JZZZL') not in (None, '') else None,
        }
    except Exception as e:
        sys.stderr.write(f'[WARN] 基金 {code} 抓取失败: {e}\n')
        return None


def fetch_gold():
    """新浪 COMEX 黄金期货（美元/盎司）。"""
    url = 'https://hq.sinajs.cn/list=hf_GC'
    try:
        req = urllib.request.Request(url, headers=SINA_HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode('gbk')
        # var hq_str_hf_GC="买价,买量,最新价,卖价,最高,最低,时间,买价2,卖价2,...,日期,名称,...";
        parts = raw.split('"')[1].split(',')
        if len(parts) < 13:
            return None
        return {
            'comex_price': float(parts[2]),
            'unit': '美元/盎司',
            'date': parts[12],
            'time': parts[6],
            'high': float(parts[4]) if parts[4] else None,
            'low': float(parts[5]) if parts[5] else None,
        }
    except Exception as e:
        sys.stderr.write(f'[WARN] 黄金抓取失败: {e}\n')
        return None


def main():
    out = {
        'updated_at': datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),
        'source': '东方财富基金净值 + 新浪COMEX金价',
        'funds': {},
        'gold': None,
    }

    for code in FUNDS:
        f = fetch_fund_nav(code)
        if f:
            out['funds'][code] = f

    g = fetch_gold()
    if g:
        out['gold'] = g

    here = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(here, '..', 'data', 'auto.json')
    with open(out_path, 'w', encoding='utf-8') as fp:
        json.dump(out, fp, ensure_ascii=False, indent=2)

    ok = len(out['funds'])
    print(f'[OK] 写入 {out_path} | 基金 {ok}/{len(FUNDS)} | 黄金 {"是" if out["gold"] else "否"}')
    print(f'[OK] 更新时间 {out["updated_at"]}')


if __name__ == '__main__':
    main()
