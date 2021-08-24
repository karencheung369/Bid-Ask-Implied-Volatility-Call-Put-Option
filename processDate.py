#!/usr/bin/env python3

import json
import csv
import sys
import os
from os import path
from dateutil import parser
from google.colab import files
import numpy as np
import matplotlib.pyplot as plt
import impliedVolatility as impvol

def processDate(filterByMinutes):
    instrumentsFile = path.join('/content/drive/My Drive/data/', 'instruments.csv')
    marketDataFile = path.join('/content/drive/My Drive/data/', 'marketdata.csv')
    #instrumentsFile = path.join(path.dirname(__file__), 'data', 'instruments.csv')
    #marketDataFile = path.join(path.dirname(__file__), 'data', 'marketdata.csv')
    instrumentList = {}
    marketList = {}
    impliedVolatilites = {}

    with open(instrumentsFile) as fileIn:
        # read instruments.csv into list
        instruments = csv.reader(fileIn)
        # skip header
        next(instruments)
        for thisRow in instruments:
            intstruType, symbol, expiry, strike, optType = thisRow
            if intstruType == 'Equity':
                continue
            instrumentList[symbol] = { 'expiry': expiry, 'strike': strike, 'optionType': optType }

    with open(marketDataFile) as fileIn:
        # read marketdata.csv into list
        markets = csv.reader(fileIn)
        # skip header
        next(markets)
        for thisRow in markets:
            time, symbol, _, bid, _, ask, _ = thisRow
            if symbol not in instrumentList:
                continue
            # use bid + ask /2 as spot price
            spot = float(bid) + float(ask) / float(2)
            # find market symbol in instrumentList to get its strike and optionType
            strike = float(instrumentList[symbol]['strike'])
            optType = instrumentList[symbol]['optionType']
            # days remaining to expiration as percentage of year
            T = (24-16)/365

            askVolCall, bidVolCall, askVolPut, bidVolPut = 0,0,0,0
            # impliedVolatility(S, K, t, T, r, C_true, q, optType)
            if optType == 'C':
                askCall_True, bidCall_True = ask, bid
                askVolCall = impvol.getImpliedVolatility(spot, strike, 0, T, 0.04, float(askCall_True), 0.2, optType)
                bidVolCall = impvol.getImpliedVolatility(spot, strike, 0, T, 0.04, float(bidCall_True), 0.2, optType)
                # print('askVolCall=' + str(askVolCall) + '    bidVolCall=' + str(bidVolCall))
        
            if optType == 'P':
                askPut_True, bidPut_True = ask, bid
                askVolPut = impvol.getImpliedVolatility(spot, strike, 0, T, 0.04, float(askPut_True), 0.2, optType)
                bidVolPut = impvol.getImpliedVolatility(spot, strike, 0, T, 0.04, float(bidPut_True), 0.2, optType)
                # print('askVolPut=' + str(askVolPut) + '    bidVolPut=' + str(bidVolPut))
            
            # if duplicated symbol for entries, append data list to marketList
            if symbol in marketList:
                marketList[symbol].append({
                    'time': time,
                    'strike': strike,
                    'bidVolPut' : bidVolPut,
                    'askVolPut' : askVolPut,
                    'bidVolCall' : bidVolCall,
                    'askVolCall' : askVolCall
                })
            else:
                marketList[symbol] = [{
                    'time': time,
                    'strike': strike,
                    'bidVolPut' : bidVolPut,
                    'askVolPut' : askVolPut,
                    'bidVolCall' : bidVolCall,
                    'askVolCall' : askVolCall
                }]
                
    # find data at each minute below
    hour, minute, second = filterByMinutes
    timeString =  str(hour) + ':' + str(minute) +  ':' + str(second)
    # instruments have distinct symbol
    for symbol in instrumentList:
        # find cooresponding marketList for symbol
        marketData = marketList[symbol]
        # index 0 to len(marketData)-1
        for index in range(0, len(marketData)):
            # find the matching minute from each marketData time
            theTime = parser.parse(marketData[index]['time'])
            if theTime.hour == hour and theTime.minute == minute and theTime.second == second:
                print ('marketData = ' + str(marketData[index]))
                
                if timeString in impliedVolatilites:
                    impliedVolatilites[timeString].append({
                    'Strike': marketData[index]['strike'],
                    'BidVolP': marketData[index]['bidVolPut'],
                    'AskVolP': marketData[index]['askVolPut'],
                    'BidVolC': marketData[index]['bidVolCall'],
                    'AskVolC': marketData[index]['askVolCall']
                })
                else:
                    impliedVolatilites[timeString] = [{
                    'Strike': marketData[index]['strike'],
                    'BidVolP': marketData[index]['bidVolPut'],
                    'AskVolP': marketData[index]['askVolPut'],
                    'BidVolC': marketData[index]['bidVolCall'],
                    'AskVolC': marketData[index]['askVolCall']
                }]
        
    # write data fetched to a csv
    csvfile=open(str(hour) + ':' + str(minute) +  ':' + str(second) + '.csv','w', newline='')
    headers=['Strike', 'BidVolP', 'AskVolP', 'BidVolC', 'AskVolC']
    obj=csv.DictWriter(csvfile, fieldnames=headers)
    obj.writeheader()
    obj.writerows(impliedVolatilites[timeString])
    csvfile.close()

    # plot by strike levels as x and implied volatilities as y
    thisMinImpVol = impliedVolatilites[timeString]
    bidVolPX, bidVolPY, askVolPX, askVolPY, bidVolCX, bidVolCY, askVolCX, askVolCY = [], [], [], [], [], [], [], []
    for index in range(0, len(thisMinImpVol)):
        strikeX = thisMinImpVol[index]['Strike']
        bidP, askP, bidC, askC = thisMinImpVol[index]['BidVolP'], thisMinImpVol[index]['AskVolP'], thisMinImpVol[index]['BidVolC'], thisMinImpVol[index]['AskVolC']
        if bidP != 0 and bidP != 'NaN':
            bidVolPX.append(strikeX)
            bidVolPY.append(bidP)
        if askP != 0 and askP != 'NaN':
            askVolPX.append(strikeX)
            askVolPY.append(askP)
        if bidC != 0 and bidC != 'NaN':
            bidVolCX.append(strikeX)
            bidVolCY.append(bidC)
        if askC != 0 and bidC != 'NaN':
            askVolCX.append(strikeX)
            askVolCY.append(askC)

    orderBPX = np.argsort(bidVolPX)
    bPX = np.array(bidVolPX)[orderBPX]
    bPY = np.array(bidVolPY)[orderBPX]
    orderAPX = np.argsort(askVolPX)
    aPX = np.array(askVolPX)[orderAPX]
    aPY = np.array(askVolPY)[orderAPX]
    orderBCX = np.argsort(bidVolCX)
    bCX = np.array(bidVolCX)[orderBCX]
    bCY = np.array(bidVolCY)[orderBCX]
    orderACX = np.argsort(askVolCX)
    aCX = np.array(askVolCX)[orderACX]
    aCY = np.array(askVolCY)[orderACX]
    fig = plt.figure()
    ax = plt.subplot(111)
    fig.suptitle(str(minute) + ' minute')
    plt.xlabel("Strike")
    plt.ylabel("Implied Volatilities")
    ax.plot(bPX, bPY, label = "BidVolP")
    ax.plot(aPX, aPY, label = "AskVolP")
    ax.plot(bCX, bCY, label = "BidVolC")
    ax.plot(aCX, aCY, label = "AskVolC")
    ax.legend()
    plt.show()

if __name__ == '__main__':
    selectMinutes = input("Generate implied volatility data for the hour:minute:second ")
    filterByMinutes = tuple(int(x) for x in selectMinutes.split(":"))
    processDate(tuple(filterByMinutes))
