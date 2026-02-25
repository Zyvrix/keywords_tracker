
import random, time

def sleep_random(a, b):
    delay = random.randint(a, b)
    time.sleep(delay)
    return delay
