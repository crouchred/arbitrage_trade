from raven import Client
import traceback
from utils.logger import Logger
logger = Logger.get_logger(__file__)

client = Client('https://459d646b66124477bce25177fa98423e:4f9edae9fbd140da82bea7f99ffd3318@sentry.io/1222147', IGNORE_EXCEPTIONS=['KeyboardInterrupt'])

def catch_decorator(func):
    def __wrapper(*args, **kwargs):
        try:
            result  = func(*args, **kwargs)
            return result
        except Exception as e:
            logger.info(traceback.format_exc())
            client.captureException()
    return __wrapper
