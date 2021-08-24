#!/usr/bin/env python3

from math import log, sqrt, exp
import scipy.stats as si
'''
    The implied volatility function is the difference between market observed option price and the Black-Scholes theoretical option price,
      root of the function is the value of the implied volatility that makes the value of the function zero. f(sigma)=0

    Newton-Raphson method converges sufficiently quickly, so we used it to find the zeros of a real valued function f(x) such that root of the function f(x)=0.
'''
def getImpliedVolatility(S, K, t, T, r, C_true, q, optType):
  if C_true == 0:
    return 'NaN'
  # (r - q) is rate of return minus dividend growth rate
  sigmahat = sqrt(2 * abs((log(S / K) + (r - q) * (T - t) ) / (T - t)))
  
  # sigma is the implied volatility
  sigma = sigmahat
  sigmadiff = 1
  # tolerance
  tol = 1e-8
  n = 1
  # max iteration in case if not converge on a solution where there is no defined 0 within function such as if market price faraway from Black Scholes solution
  nMax = 100
  while sigmadiff >= tol and n < nMax:
      C = blackSchEuro(S, K, t, T, r, sigma, q, 'call')
      # vega is the sensitivity of black scholes price with respect to change in sigma
      Cprime = vega(S, K, t, T, r, sigma, q)
      # signma new = sigma old - (black scholes price calculated at this sigma - current market price / vega)
      increment = (C - C_true) / Cprime
      sigma = sigma - increment
      n += 1
      # result requires the starting value x0 is suciently close to x, otherwise it may fail to converge
      sigmadiff = abs(increment)
  # implied volatility for some instrument is not achievable
  if n >= nMax and sigmadiff < tol:
      return 'NaN'
  return round(sigma, 4)

def blackSchEuro(S, K, t, T, r, sigma, q, optType):
    d1 = (log(S / K) + (r - q) * (T - t)) / (sigma * sqrt(T - t)) + 0.5 * sigma * sqrt(T - t)
    d2 = (log(S / K) + r * (T - t)) / (sigma * sqrt(T - t)) - 0.5 * sigma * sqrt(T - t)
    
    if optType == 'call':
      callOpt = (S * (exp (-q * (T - t))) * si.norm.cdf(d1, 0.0, 1.0) - K * (exp (-r * (T - t))) * si.norm.cdf(d2, 0.0, 1.0))
      return round(callOpt, 4)   
    if optType == 'put':
      putOpt = (K * (exp (-r * (T - t))) * si.norm.cdf(-d2, 0.0, 1.0) - S * (exp (-q * (T - t))) * si.norm.cdf(-d1, 0.0, 1.0))
      return round(putOpt, 4)

def vega(S, K, t, T, r, sigma, q):
    # vega_put = vega_call as by put-call parity, put and call must have the same vega
    d1 = (log(S / K) + (r + 0.5 * (sigma ** 2)) * T) / (sigma * sqrt(T))
    return S * (exp (-q * (T - t))) * sqrt(T - t) * si.norm.cdf(d1, 0.0, 1.0)
