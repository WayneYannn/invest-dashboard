#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
宏观经济数据抓取脚本（PMI / CPI / PPI）

数据源：东方财富 datacenter-web API（已验证可用）
  - CPI: RPT_ECONOMY_CPI  → 居民消费价格指数（同比/环比）
  - PPI: RPT_ECONOMY_PPI  → 工业品出厂价格指数（同比）
  - PMI: RPT_ECONOMY_PMI  → 采购经理人指数（制造业/非制造业）

频率：月度更新（数据每月发布一次）。可手动跑或挂 Actions 月度触发。
输出：写入 data/macro.json
"""
import urllib.request
import json
import datetime
import os

HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
API = "https://datacenter-web.eastmoney.com/api/data/v1/get"

def fetch(report_name, size=24):
    """抓取指定报表最近 N 期数据"""
    url = f"{API}?reportName={report_name}&columns=ALL&pageNumber=1&pageSize={size}&sortColumns=REPORT_DATE&sortTypes=-1"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        d = json.loads(resp.read().decode('utf-8'))
    if not d.get('success') or not d.get('result'):
        return []
    result = d['result']
    return result.get('data', []) if isinstance(result, dict) else result

def parse_cpi():
    """CPI：取同比(NATIONAL_SAME)和环比(NATIONAL_SEQUENTIAL)"""
    rows = fetch('RPT_ECONOMY_CPI', 24)
    out = []
    for r in rows:
        out.append({
            'date': r.get('REPORT_DATE', '')[:10],
            'label': r.get('TIME', ''),
            'yoy': r.get('NATIONAL_SAME'),      # 同比%
            'mom': r.get('NATIONAL_SEQUENTIAL')  # 环比%
        })
    return out

def parse_ppi():
    """PPI：取同比(BASE_SAME)"""
    rows = fetch('RPT_ECONOMY_PPI', 24)
    out = []
    for r in rows:
        out.append({
            'date': r.get('REPORT_DATE', '')[:10],
            'label': r.get('TIME', ''),
            'yoy': r.get('BASE_SAME')            # 同比%
        })
    return out

def parse_pmi():
    """PMI：制造业(MAKE_INDEX)和非制造业(NMAKE_INDEX)"""
    rows = fetch('RPT_ECONOMY_PMI', 24)
    out = []
    for r in rows:
        out.append({
            'date': r.get('REPORT_DATE', '')[:10],
            'label': r.get('TIME', ''),
            'mfg': r.get('MAKE_INDEX'),          # 制造业PMI
            'non_mfg': r.get('NMAKE_INDEX')      # 非制造业PMI
        })
    return out

def main():
    print("抓取宏观经济数据（PMI/CPI/PPI）...")
    try:
        cpi = parse_cpi()
        ppi = parse_ppi()
        pmi = parse_pmi()
        if not cpi or not ppi or not pmi:
            print("⚠️ 部分数据抓取失败")
        out = {
            'updated_at': datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S+08:00'),
            'source': 'eastmoney_datacenter',
            'cpi': cpi,
            'ppi': ppi,
            'pmi': pmi
        }
        out_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'macro.json')
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print(f"✓ 写入 {out_path}")
        print(f"  CPI: {len(cpi)}期, 最新 {cpi[0]['label'] if cpi else 'N/A'} 同比 {cpi[0]['yoy'] if cpi else 'N/A'}%")
        print(f"  PPI: {len(ppi)}期, 最新 {ppi[0]['label'] if ppi else 'N/A'} 同比 {ppi[0]['yoy'] if ppi else 'N/A'}%")
        print(f"  PMI: {len(pmi)}期, 最新 {pmi[0]['label'] if pmi else 'N/A'} 制造业 {pmi[0]['mfg'] if pmi else 'N/A'}")
    except Exception as e:
        print(f"✗ 抓取失败: {e}")
        # 失败时写一个空文件标记，看板降级处理
        out_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'macro.json')
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump({'updated_at': '', 'source': 'eastmoney_datacenter', 'cpi': [], 'ppi': [], 'pmi': [], 'error': str(e)}, f, ensure_ascii=False, indent=2)
        raise

if __name__ == '__main__':
    main()
