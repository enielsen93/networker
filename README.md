# networker
Python Package for getting fromnode and tonode in a MIKE URBAN Database by spatial analysis. Useful for when pipes, orifices and weirs do not have or have in incorrect fromnode and tonode values (i.e. when the Project Check Tool has not been run).

<b>To install:</b>

```
python -m pip install https://github.com/enielsen93/networker/tarball/master
```

## Example:
```
import networker

MU_database = r"C:\Mike Model.mdb"
network = networker.NetworkLinks(MU_database, map_only = map_only)

for link in network.links:
  print("Link %s reaches from %s to %s" % (link, network.links[link].fromnode, network.links[link].tonode))
```
