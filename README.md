# twarc-report
Data conversions and examples for generating reports from [twarc](https://github.com/edsu/twarc) collections using tools such as D3.js

These utilities accept a Twitter json file (as fetched by twarc), analyze it various ways, and output 
a json or csv file. The initial purpose is to feed data into D3.js for various visualizations,
but the intention is to make the outputs generic enough to serve other uses as well. Each utility 
also has a D3 example template, which it can use to generate a self-contained html file.

The directed.py utility was originally added to the twarc repo but is moving here for consistency.

## D3 visualizations

Some utilities to generate [D3](http://d3js.org/) visualizations of aspects of a collection
of tweets are provided. Use "--output=json" or "--output=csv" to output the data for use with 
other D3 examples, or "--help" for other options.

A directed graph of mentions
or retweets, in which nodes are users and arrows point from the original user
to the user who mentions or retweets them:

    % directed.py --mode mentions nasa-20130306102105.json > nasa-directed-mentions.html
    % directed.py --mode retweets nasa-20130306102105.json > nasa-directed-retweets.html
    % directed.py --mode replies nasa-20130306102105.json > nasa-directed-replies.html
    
A bar chart timeline with arbitrary intervals:

    % d3times.py -a -t local -i 5M nasa-20130306102105.json > nasa-timebargraph.html

[Examples](https://wallandbinkley.com/twarc/bill10/)

The output timezone is specified by -t; the interval is specified by -i, using the 
[standard abbreviations](https://docs.python.org/2/library/time.html#time.strftime): 
seconds = S, minutes = M, hours = H, days = d, months = m, years = Y. The example above 
uses five-minute intervals.

License
-------

* CC0

