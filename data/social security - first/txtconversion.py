import pandas as pd
import csv

file_list = ['yob1882.txt', 'yob1883.txt', 'yob1884.txt', 'yob1885.txt', 'yob1886.txt', 'yob1887.txt', 'yob1888.txt', 'yob1889.txt', 'yob1890.txt', 'yob1891.txt', 'yob1892.txt', 'yob1893.txt', 'yob1894.txt', 'yob1895.txt', 'yob1896.txt', 'yob1897.txt', 'yob1898.txt', 'yob1899.txt', 'yob1900.txt', 'yob1901.txt', 'yob1902.txt', 'yob1903.txt', 'yob1904.txt', 'yob1905.txt', 'yob1906.txt', 'yob1907.txt', 'yob1908.txt', 'yob1909.txt', 'yob1910.txt', 'yob1911.txt', 'yob1912.txt', 'yob1913.txt', 'yob1914.txt', 'yob1915.txt', 'yob1916.txt', 'yob1917.txt', 'yob1918.txt', 'yob1919.txt', 'yob1920.txt', 'yob1921.txt', 'yob1922.txt', 'yob1923.txt', 'yob1924.txt', 'yob1925.txt', 'yob1926.txt', 'yob1927.txt', 'yob1928.txt', 'yob1929.txt', 'yob1930.txt', 'yob1931.txt', 'yob1932.txt', 'yob1933.txt', 'yob1934.txt', 'yob1935.txt', 'yob1936.txt', 'yob1937.txt', 'yob1938.txt', 'yob1939.txt', 'yob1940.txt', 'yob1941.txt', 'yob1942.txt', 'yob1943.txt', 'yob1944.txt', 'yob1945.txt', 'yob1946.txt', 'yob1947.txt', 'yob1948.txt', 'yob1949.txt', 'yob1950.txt', 'yob1951.txt', 'yob1952.txt', 'yob1953.txt', 'yob1954.txt', 'yob1955.txt', 'yob1956.txt', 'yob1957.txt', 'yob1958.txt', 'yob1959.txt', 'yob1960.txt', 'yob1961.txt', 'yob1962.txt', 'yob1963.txt', 'yob1964.txt', 'yob1965.txt', 'yob1966.txt', 'yob1967.txt', 'yob1968.txt', 'yob1969.txt', 'yob1970.txt', 'yob1971.txt', 'yob1972.txt', 'yob1973.txt', 'yob1974.txt', 'yob1975.txt', 'yob1976.txt', 'yob1977.txt', 'yob1978.txt', 'yob1979.txt', 'yob1980.txt', 'yob1981.txt', 'yob1982.txt', 'yob1983.txt', 'yob1984.txt', 'yob1985.txt', 'yob1986.txt', 'yob1987.txt', 'yob1988.txt', 'yob1989.txt', 'yob1990.txt', 'yob1991.txt', 'yob1992.txt', 'yob1993.txt', 'yob1994.txt', 'yob1995.txt', 'yob1996.txt', 'yob1997.txt', 'yob1998.txt', 'yob1999.txt', 'yob2000.txt', 'yob2001.txt', 'yob2002.txt', 'yob2003.txt', 'yob2004.txt', 'yob2005.txt', 'yob2006.txt', 'yob2007.txt', 'yob2008.txt', 'yob2009.txt', 'yob2010.txt', 'yob2011.txt', 'yob2012.txt', 'yob2013.txt', 'yob2014.txt', 'yob2015.txt', 'yob2016.txt', 'yob2017.txt']


for file in file_list:
	
	df = pd.read_csv(file, delimiter=',', names=["first", "sex", "occurences"])
	
	csv_name = file[:-4] + ".csv"
	year = file[3:-4]

	df['year'] = year
	
	df.to_csv(csv_name, index=False)