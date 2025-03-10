#!/usr/bin/bash


cd matrices
wget https://suitesparse-collection-website.herokuapp.com/MM/Norris/stomach.tar.gz
wget https://suitesparse-collection-website.herokuapp.com/MM/DIMACS10/delaunay_n22.tar.gz

tar -xzf stomach.tar.gz && rm stomach.tar.gz
tar -xzf delaunay_n22.tar.gz && rm delaunay_n22.tar.gz
