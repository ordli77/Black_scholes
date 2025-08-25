from utils import BS, find_vol
import numpy
import math

def test_closed_form_atm():
    S,K,r,sigma,T,q = 100,100,0.05,0.2,1.0,0.0
    c = BS(S,K,T,r,sigma,'call')
    p = BS(S,K,T,r,sigma,'put')
    assert abs(c - 10.450583572185565) < 1e-10
    assert abs(p -  5.573526022256971) < 1e-10

def test_put_call_parity():
    S,K,r,sigma,T,q = 100,110,0.03,0.25,0.5,0.01
    c = BS(S,K,T,r,sigma,'call')
    p = BS(S,K,T,r,sigma,'put')
    assert abs((c - p) - (S - K*math.exp(-r*T))) < 1e-10

def test_iv_roundtrip():
    S,K,r,T,q = 100,105,0.02,0.75,0.00
    true_sigma = 0.32
    mkt = BS(S,K,T,r,true_sigma,'call')
    iv = find_vol(mkt,S,K,T,r,'call')
    recon = BS(S,K,T,r,iv,'call')
    assert abs(iv - true_sigma) < 1e-7
    assert abs(recon - mkt) < 1e-10