QuantFinan
==========
Python codes to test different algorithms used in quantitative finance. 

As the first example, the Momentum algorithm is implemented. 
This algorithm picks up the stocks with largest momentum from the 
S&P 500 list. The required external python packages is 
[snp500](https://github.com/yangphysics/snp500).

To test it on the terminal, first you would need to prepare the data-base containing
the historical stock information for companies listed in the S&P 500 from Yahoo Finance.
```bash
    python database.py
```
This step might take more than ten minutes depending on the quality of your internet connection.

After the database is prepared, you could go ahead and run the momentum code as
```bash
    python momentum.py
```
