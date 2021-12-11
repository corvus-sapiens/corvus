"""Setup for the 'corvus' package"""


import setuptools  # type: ignore

with open("VERSION", "r", encoding="utf-8") as file:
    version = file.read().strip()

with open("requirements.txt", "r", encoding="utf8") as file:
    requirements = [line.strip() for line in file if line]

setuptools.setup(
    name='corvus',
    version=version,
    description='An assortment of convenience tools',
    url='#',
    author='Alexander Gorelyshev',
    install_requires=requirements,
    author_email='alexander.gorelyshev@pm.me',
    packages=setuptools.find_packages(),
    zip_safe=False
)
