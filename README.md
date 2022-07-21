# networker
Python Package for analyzing fromnode and tonode in a Mike Urban Database

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
