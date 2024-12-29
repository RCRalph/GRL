# GRL - Graph Representation Language

GRL is an interpreted language, which has the following features:
- creating and manipulating graphs and their properties
- running graph algorithms
- importing and exporting graphs using the `.grlg` format
- running previously prepared scripts
- performing calculations using if/elseif/else statements and for loops

## Examples
```
ADD GRAPH my_graph
ADD NODE "A" my_graph
ADD NODE "B" my_graph
ADD EDGE "A" "B" my_graph
SET WEIGHT OF EDGE "A" "B" 5 my_graph

PRINT NODE COUNT my_graph
PRINT "\n"

PRINT EDGE COUNT my_graph
PRINT "\n"

FOR node OF NODES my_graph { PRINT node; PRINT "\n"}

DRAW my_graph
```

More example scripts can be found inside the `examples` directory.
