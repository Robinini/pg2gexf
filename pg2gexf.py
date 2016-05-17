'''
Python code to extract data from a PostGIS server and save as 
Gephi .gexf XML Format.

PostGIS data must be prepared with osm2po-5.0.0, in accordance with 
FHNW MSE Vertiefungsmodul GIT_mobileGI FS2016
"Routing mit pgRouting in PostgreSQL auf Basis freier Geodaten"

Robin Dainton
FHNW 10.5.2016

'''

import datetime
import psycopg2
from lxml.etree import Element, SubElement, Comment, tostring

# Database connection parameters
database = 'routing'
user = 'postgres'
password = 'postgres'
host = 'localhost'
port = 5432

# Output filename
outfile = r'basel.gexf'


##########################################################
# Function to excecute SQL query and return row list
def pg_query(sql):
    cur = conn.cursor()
    cur.execute(sql)
    return cur.fetchall()


#################################################
# Procedural code starts here

date = datetime.date.today().strftime("%Y-%m-%d")

try:
    conn = psycopg2.connect(host=host, port=port, database=database, user=user, password=password)

except:
    exit("I am unable to connect to the database")

file = open(outfile, "w")

# Create XML Tree Root Node
root = Element('gexf')
root.set('xmlns', 'http://www.gexf.net/1.2draft')
root.set('version', '1.2')

# Create XML Meta Node
meta = SubElement(root, 'meta')
meta.set('lastmodifieddate', date)

creator = SubElement(meta, 'creator')
creator.text = 'Robin Dainton, Thomas Gerzner FHNW'

description = SubElement(meta, 'description')
description.text = 'MSE FS16 Semesterprojekt FHNW'

##################################################################
# Create XML Tree Graph Node
graph = SubElement(root, 'graph')
graph.set('mode', 'static')
graph.set('defaultedgetype', 'directed')

# Create XML Tree Nodes Node
nodes = SubElement(graph, 'nodes')
attributes = SubElement(nodes, 'attributes')
attributes.set('class', 'node')

# Define Node attribute types
attribute = SubElement(attributes, 'attribute')
attribute.set('id', '0')
attribute.set('title', 'lat')
attribute.set('type', 'float')

attribute = SubElement(attributes, 'attribute')
attribute.set('id', '1')
attribute.set('title', 'lon')
attribute.set('type', 'float')

# SQL Query fur Node infomrmation
   # sql_nodes = "SELECT osm_id, ST_X(way) as X, ST_Y(way) as y FROM planet_osm_point where osm_id in (SELECT osm_source_id FROM basel_2po_4pgr UNION SELECT osm_target_id FROM basel_2po_4pgr)"
# Problem - topologie nodes sind nicht in planet_osm_point importiert. Mussen aus Ways generiert:
sql_nodes = '''SELECT osm_source_id,
                ST_X(ST_StartPoint(geom_way)) as X,
                ST_Y(ST_StartPoint(geom_way)) as y 
                FROM basel_2po_4pgr 
                WHERE osm_source_id is not NULL
                UNION SELECT osm_target_id,
                ST_X(ST_EndPoint(geom_way)) as X,
                ST_Y(ST_EndPoint(geom_way)) as y 
                FROM basel_2po_4pgr 
                WHERE osm_target_id is not NULL
                AND osm_target_id not in (SELECT osm_source_id FROM basel_2po_4pgr)'''

# Excecute query 
rows = pg_query(sql_nodes)

for row in rows:
    ident = row[0]
    X = row[1]
    Y = row[2]

    # add Node to XML
    node = SubElement(nodes, 'node')
    node.set('id', str(ident))
    node.set('label', str(ident))
    attvalues = SubElement(node, 'attvalues')
    attvalue = SubElement(attvalues, 'attvalue')
    attvalue.set('for', '0') #lat
    attvalue.set('value', str(Y))
    attvalue = SubElement(attvalues, 'attvalue')
    attvalue.set('for', '1') # lon
    attvalue.set('value', str(X))

print str(len(rows)) + " nodes generated"

#############################################################
# Create XML Tree Edges Node
edges = SubElement(graph, 'edges')
attributes = SubElement(edges, 'attributes')
attributes.set('class', 'edge')

# Define Edge attribute types
attribute = SubElement(attributes, 'attribute')
attribute.set('id', '0')
attribute.set('title', 'clazz')
attribute.set('type', 'integer')

attribute = SubElement(attributes, 'attribute')
attribute.set('id', '1')
attribute.set('title', 'km')
attribute.set('type', 'float')

attribute = SubElement(attributes, 'attribute')
attribute.set('id', '2')
attribute.set('title', 'kmh')
attribute.set('type', 'integer')

attribute = SubElement(attributes, 'attribute')
attribute.set('id', '3')
attribute.set('title', 'cost')
attribute.set('type', 'float')

attribute = SubElement(attributes, 'attribute')
attribute.set('id', '4')
attribute.set('title', 'reverse_cost')
attribute.set('type', 'float')


# SQL Befehle fur edges
sql_edges = '''SELECT id,
                clazz,
                osm_source_id,
                osm_target_id,
                km,
                kmh,
                cost,
                reverse_cost,
                osm_name
                FROM basel_2po_4pgr'''

# Excecute query               
rows = pg_query(sql_edges)

for row in rows:
    ident = row[0]
    clazz = row[1]
    osm_source_id = row[2]
    osm_target_id = row[3]
    km = row[4]
    kmh = row[5]
    cost = row[6]
    if cost == 0:
        cost = 0.000001 # To avoid edge being ignored
    reverse_cost = row[7]
    name = row[8]

    # add Edge to XML
    edge = SubElement(edges, 'edge')
    edge.set('id', str(ident))
    if (False and name and len(name) > 0): # Problem uemlauts
        edge.set('label', name)
    edge.set('source', str(osm_source_id))
    edge.set('target', str(osm_target_id))
    edge.set('weight', str(1/float(clazz)))
    attvalues = SubElement(edge, 'attvalues')
    attvalue = SubElement(attvalues, 'attvalue')
    attvalue.set('for', '0') #clazz
    attvalue.set('value', str(clazz))
    attvalue = SubElement(attvalues, 'attvalue')
    attvalue.set('for', '1') #km
    attvalue.set('value', str(km))
    attvalue = SubElement(attvalues, 'attvalue')
    attvalue.set('for', '2') #kmh
    attvalue.set('value', str(kmh))
    attvalue = SubElement(attvalues, 'attvalue')
    attvalue.set('for', '3') #cost
    attvalue.set('value', str(cost))
    attvalue = SubElement(attvalues, 'attvalue')
    attvalue.set('for', '4') #reverse_cost
    attvalue.set('value', str(reverse_cost))
print str(len(rows)) + " edges generated"

########################################################################
# Writefile
xml_string = tostring(root, encoding='utf8', method='xml', pretty_print=True)
file.write(xml_string)
file.close


print "Done!"
