from redisio import Redis

__version__ = '0.3'
VERSION = tuple(map(int, __version__.split('.')))
__all__ = ['Redis']
