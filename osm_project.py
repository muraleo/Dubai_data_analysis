import csv
import codecs
import pprint
import re
import xml.etree.cElementTree as ET

import cerberus

import schema

OSM_PATH = "dubai_abu-dhabi.osm"

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

SCHEMA = schema.schema

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']

street_mapping = { "St": "Street",
						"St.": "Street",
						"Ave": "Avenue",
						"Rd.": "Road",
						"road": "Road"
						}

key_mapping = {
		"motorcar": "motor_vehicle",
		"old_name_1": "old_name",
		"old_name_2": "old_name",
		"phone_1":" phone"
}

#Bad characters in phone numbers
phone_bad_char = [" ", "+", "-", "(", ")"]

def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
									problem_chars=PROBLEMCHARS, default_tag_type='regular'):
		"""Clean and shape node or way XML element to Python dict"""

		node_attribs = {}
		way_attribs = {}
		way_nodes = []
		tags = []  # Handle secondary tags the same way for both node and way elements

		# YOUR CODE HERE
		if element.tag == 'node':
			for field in node_attr_fields:
				node_attribs[field] = element.attrib[field]
			for sub_field in element:
				tag = {}
				'''if the tag "k" value contains problematic characters, the tag should be ignored'''
				if PROBLEMCHARS.search(sub_field.attrib['k']):
					continue
				elif str(':') in sub_field.attrib['k']:
					temp = sub_field.attrib['k'].split(":", 1)
					tag['id'] = element.attrib['id']
					tag['key'] = temp[1]
					tag['value'] = sub_field.attrib['v']
					tag['type'] = temp[0]
					tags.append(tag)
				else:
						tag['id'] = element.attrib['id']
						tag['key'] = sub_field.attrib['k']
						tag['value'] = sub_field.attrib['v']
						tag['type'] = default_tag_type
						tags.append(tag)
						
				'''If a node has no secondary tags then the "node_tags" field should just contain an empty list.'''
							
			return {'node': node_attribs, 'node_tags': tags}
		elif element.tag == 'way':
			for field in way_attr_fields:
				way_attribs[field] = element.attrib[field]
			count = 0
			for sub_field in element:
				tag = {}
				w_node = {}
				if sub_field.tag == 'tag':
					if PROBLEMCHARS.search(sub_field.attrib['k']):
							continue
					elif ":" in sub_field.attrib['k']:
							temp = sub_field.attrib['k'].split(":", 1)
							tag['id'] = element.attrib['id']
							tag['key'] = temp[1]
							tag['value'] = sub_field.attrib['v']
							tag['type'] = temp[0]
							tags.append(tag)
					else:
							tag['id'] = element.attrib['id']
							tag['key'] = sub_field.attrib['k']
							tag['value'] = sub_field.attrib['v']
							tag['type'] = default_tag_type
							tags.append(tag)
				elif sub_field.tag == 'nd':
						w_node['id'] = element.attrib['id']
						w_node['node_id'] = sub_field.attrib['ref']
						w_node['position'] = count
						count+=1
						way_nodes.append(w_node)
			return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}

# Unify key' format
def better_key(key):
	if key_mapping.has_key(key):
		return key_mapping[key]
	else:
		return key

# Unify value format
def better_value(key, value):
	if key == "addr:street":
		value = update_street_name(value, street_mapping)
		return value
	elif key == "addr:city":
		value = update_city_name(value)
		return value
	elif key == "phone":
		value = update_phone_name(value, phone_bad_char)
		return value
	else:
		return value

def update_street_name(street_name, street_mapping):
		result = street_name
		if "Steet" in street_name:
			result = street_name.replace("Steet", "Street")
			return result
		else:
			for c in street_mapping:
				if c in street_name and street_mapping[c] not in street_name:
					result = street_name.replace(c, street_mapping[c])
					break # not jump out of if statement, but jump out of the whole for loop
		return result

def update_city_name(value):
	if value == 'DUBAI':
		return 'Dubai'
	else:
		return value

def update_phone_name(number, phone_bad_char):
	for bc in phone_bad_char:
		if bc in number:
			number = number.replace(bc, "")
	return number

def audit_element(elem):
	if elem.tag == 'node':
		for k in elem:
			k.attrib['k'] = better_key(k.attrib['k'])
			k.attrib['v'] = better_value(k.attrib['k'], k.attrib['v'])
	elif  elem.tag == 'way':
		for k in elem:
			if k.attrib.has_key('k'):
				k.attrib['k'] = better_key(k.attrib['k'])
				k.attrib['v'] = better_value(k.attrib['k'], k.attrib['v'])
	return elem


# ================================================== #
#               Helper Functions                     #
# ================================================== #
def get_element(osm_file, tags=('node', 'way', 'relation')):
		"""Yield element if it is the right type of tag"""

		context = ET.iterparse(osm_file, events=('start', 'end'))
		_, root = next(context)
		for event, elem in context:
			if event == 'end' and elem.tag in tags:
				yield elem
				root.clear()


def validate_element(element, validator, schema=SCHEMA):
	"""Raise ValidationError if element does not match schema"""
	if validator.validate(element, schema) is not True:
		field, errors = next(validator.errors.iteritems())
		message_string = "\nElement of type '{0}' has the following errors:\n{1}"
		error_string = pprint.pformat(errors)
		
		raise Exception(message_string.format(field, error_string))


class UnicodeDictWriter(csv.DictWriter, object):
	"""Extend csv.DictWriter to handle Unicode input"""

	def writerow(self, row):
		super(UnicodeDictWriter, self).writerow({
				k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
		})

	def writerows(self, rows):
		for row in rows:
				self.writerow(row)

# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate):
	"""Iteratively process each XML element and write to csv(s)"""

	with codecs.open(NODES_PATH, 'w') as nodes_file, \
		 codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
		 codecs.open(WAYS_PATH, 'w') as ways_file, \
		 codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
		 codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

		nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
		node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
		ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
		way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
		way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

		nodes_writer.writeheader()
		node_tags_writer.writeheader()
		ways_writer.writeheader()
		way_nodes_writer.writeheader()
		way_tags_writer.writeheader()

		validator = cerberus.Validator()

		for element in get_element(file_in, tags=('node', 'way')):
			better_element = audit_element(element)
			el = shape_element(better_element)
			if el:
				if validate is True:
					validate_element(el, validator)

				if element.tag == 'node':
					nodes_writer.writerow(el['node'])
					node_tags_writer.writerows(el['node_tags'])
				elif element.tag == 'way':
					ways_writer.writerow(el['way'])
					way_nodes_writer.writerows(el['way_nodes'])
					way_tags_writer.writerows(el['way_tags'])

if __name__ == '__main__':
	# Note: Validation is ~ 10X slower. For the project consider using a small
	# sample of the map when validating.
	process_map(OSM_PATH, validate=False)