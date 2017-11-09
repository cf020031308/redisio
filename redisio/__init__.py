from redisio import Redis

__version__ = '0.6'
VERSION = tuple(map(int, __version__.split('.')))
__all__ = ['Redis']
