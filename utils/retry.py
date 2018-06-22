import time 
import traceback

def retry(times=3, exception=Exception):
    def __decorator(func):
        def __wrapper(*args, **kwargs):
            for i in range(times):
                try:
                    result  = func(*args, **kwargs)
                    return result
                except exception as e:
                    print("the %s times to retry: %s"%(i, traceback.format_exc()))
                    time.sleep(2)
                    if i+1 == times:
                        raise
        return __wrapper
    return __decorator
