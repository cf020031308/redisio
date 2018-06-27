from distutils.core import setup

from redisio import __version__

me = 'Roy'
email = 'cf020031308@163.com'
with open('README.md') as file:
    desc = file.read()

setup(
    name='redisio',
    version=__version__,
    author=me,
    author_email=email,
    maintainer=me,
    maintainer_email=email,
    packages=['redisio'],
    url='https://github.com/cf020031308/redisio',
    keywords=['Redis', 'key-value store'],
    license='MIT',
    description=(
        'A tiny redis client for script boys with high performance. '
        'Optimized especially for massive insertion.'),
    long_description=desc,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Topic :: Database'
    ]
)
