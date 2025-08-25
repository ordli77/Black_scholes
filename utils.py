import numpy as np
import pandas as pd
import math
import matplotlib.pyplot as plt
from scipy.stats import norm


def GBM (S0,mu,sigma,T,N,m):
    #simulate the geometric brownian motion path of the stock price
    dt = T/N
    
    ST =  np.exp((mu- sigma**2 / 2)*dt + sigma* np.random.normal(0,np.sqrt(dt),size=(N,m)))

    ST = S0 * ST.cumprod(axis=0)
    return ST

def BS (S, K, T, r, sigma,option="call"):
    #calculate the option price using Black-Scholes
    d1= (np.log(S/K)+( r+ sigma**2 / 2)*T)/(sigma*np.sqrt(T))
    d2= d1-sigma*np.sqrt(T)
                                            
    if option == "call":
        return  S*norm.cdf(d1)- K*np.exp(-r*T)*norm.cdf(d2)
    else :
        return  K*np.exp(-r*T)*norm.cdf(-d2)- S*norm.cdf(-d1)

def BS_vega(S, K, T, r, sigma):
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    return S * norm.pdf(d1) * np.sqrt(T)


def find_vol(mkt_value, S, K, T, r, *args):
    #find implied volatility using Newton's method
    MAX_ITERATIONS = 200
    PRECISION = 1.0e-5
    sigma = 0.5
    for i in range(0, MAX_ITERATIONS):
        price = BS(S, K, T, r, sigma)
        vega = BS_vega(S, K, T, r, sigma)
        diff = mkt_value - price  # our root
        if (abs(diff) < PRECISION):
            return sigma
        sigma = sigma + diff/vega # f(x) / f'(x)
    return sigma 