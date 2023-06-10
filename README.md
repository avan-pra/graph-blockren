To use the project, a `neo4j` database must be available to you, the default password in the programm is `password`
To run a neo4j database, run
```
docker run \            
    --publish=7474:7474 --publish=7687:7687 \
    --volume=$HOME/.neo4j/data:/data \
    -d neo4j
```
Then go to http://localhost:7474/browser/ and change the password to `password` (or whatever you want)

Example:
```bash
$ python3 main.py fetch -c https://rpc.sepolia.org/ -r 3529374-3529379
Fetching a total of 6 block (from 3529374 to 3529379)
Writing blocks to /tmp/tmpkzjtmsea
Wrote 6 block (from 3529374 to 3529379) to /tmp/tmpkzjtmsea
$ python3 main.py import -f /tmp/tmpkzjtmsea                          
Connected to bolt://localhost:7687
Importing 186 transactions
Done
```

Then go to http://localhost:7474/browser/ and query with `match (n) return n`
You should see smth like this
![exampleimg](https://cdn.discordapp.com/attachments/462676451045408768/1117003294167011358/image.png)
