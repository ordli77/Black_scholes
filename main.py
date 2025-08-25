from utils import BS,BS_vega,find_vol
from tests.tests import  test_put_call_parity

def demo(S,K,T,r,sigma):
    
    call_price = BS(S, K, T, r, sigma, option="call")
    #put_price  = BS(S, K, T, r, sigma, option="put")
    print(f"Call price = {call_price:.4f}")
    #print(f"Put  price = {put_price:.4f}")

if __name__ == "__main__":
    S, K, T, r, sigma = 100, 100, 1, 0.05, 0.2
    demo(S, K, T, r, sigma)
    test_put_call_parity()