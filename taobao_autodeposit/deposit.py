# -*- coding: utf-8 -*-
import time
import requests
import top.api
from settings import (APP_KEY, SECRET, SESSION_KEY, 
                      AUTH_USER, AUTH_PASSWORD, GATEWAYD_REST_API, 
                      CURRENCY, ISSUER)

top.setDefaultAppInfo(APP_KEY, SECRET)

def get_new_orders():
    """获取新订单"""
    tids = []
    req = top.api.LogisticsOrdersGetRequest()
    req.fields="tid,out_sid,created,modified,status,freight_payer,seller_confirm,company_name"
    req.status="CREATED"
    try:
        resp = req.getResponse(SESSION_KEY)
        if resp['logistics_orders_get_response']['total_results'] == 0:
            return tids

        shipping = resp['logistics_orders_get_response']['shippings']['shipping']
        for item in shipping:
            tids.append(item["tid"])
    except Exception, e:
        print(e)

    if tids:
        print "检测到订单:", tids
    return tids
        
def send(tid):
    """发货"""
    result = False
    req = top.api.LogisticsDummySendRequest()
    req.tid = tid
    try:
        resp = req.getResponse(SESSION_KEY)
        result = resp['logistics_dummy_send_response']['shipping']['is_success']
        print "订单%s发送%s" % (tid, {True:"成功", False:"失败"}.get(result))
    except Exception, e:
        print(e)

    return result 

def get_detail(tid):
    res = {}
    req = top.api.TradeGetRequest()
    req.fields="orders.total_fee,buyer_message"
    req.tid=tid
    try:
        resp = req.getResponse(SESSION_KEY)
        res = {
            'buyer_message': resp['trade_get_response']['trade']['buyer_message'],
            'total_fee': resp['trade_get_response']['trade']['orders']['order'][0]['total_fee']
        }
    except Exception, e:
        print(e)

    return res

def send_cny(data):
    address = data['buyer_message']
    amount = data['total_fee']
    auth = (AUTH_USER, AUTH_PASSWORD)
    payload = {
        'currency': CURRENCY,
        'amount': amount,
        'address': address,
        'issuer': ISSUER 
    } 

    r = requests.post('%sv1/payments/outgoing' % GATEWAYD_REST_API, auth=auth, data=payload, verify=False)
    if r.status_code == 200:
        print r.json()
        return True
    else:
        print r.text
        return False

def process(tid): 
    """根据订单号，发送CNY到订单中的地址"""
    data = get_detail(tid)
    print data
    if data:
        send_cny(data)


def main():
    while True:
        tids =  get_new_orders()
        if tids:
            for tid in tids:
                send(tid) and process(tid)

        print "没有花香，没有树高，休息3秒先(*^__^*) ……"
        time.sleep(3);

if __name__ == "__main__":
    main()
