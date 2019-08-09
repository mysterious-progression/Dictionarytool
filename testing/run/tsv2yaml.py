#!/usr/bin/env python3 

from pandas import read_csv
import argparse
import ruamel.yaml
from ruamel.yaml import YAML
import re
import os
import math
import schema_utils
from schema_utils import stripper

S = ruamel.yaml.scalarstring.DoubleQuotedScalarString
def get_params():
    """Gets arguments entered from the commandline and returns them as a object containing their references."""

    parser = argparse.ArgumentParser(description="name of directory containing target nodes, uses enum and nodeterms, and variables TSV files, and name of output dictionary.")
    parser.add_argument("-noterms", "--noterms", dest="noterms", required=False, help="Location of the nodes tsv")
    parser.add_argument("-nodes", "--nodes", dest="nodes", required=True, help="Location of the nodes tsv")
    parser.add_argument("-var", "--variables", dest="variables", required=True, help="Location of the variables tsv")
    parser.add_argument("-out", "--output", dest="output", required=True, help="Location of the variables tsv")
    
    args = parser.parse_args()

    return args

def buildnode(node, terms):
    """Builds a python dictionary that will be used as a template for constructing nodes. Values are added to this stucture and
    this is the dictionary that will be used to dump to a yaml file"""
    
    if node['<category>'] == 'data_file':
        sy = ['id', 'project_id', 'state', 'created_datetime', 'updated_datetime', 'state', 'file_state', 'error_type']
    else:
        sy = ['id', 'project_id', 'state', 'created_datetime', 'updated_datetime']
    d = [["id"], ["project", "file"]]
    
    outdict = {'$schema': "http://json-schema.org/draft-04/schema#",
    'id': S(validate_node_name(node['<node>'])),
    'title': node['<title>'],
    'type': 'object',
    'nodeTerms': get_terms(node.get('<nodeTerms>')),
    'namespace': node['<namespace>'],
    'category': node['<category>'],
    'program': '*',
    'project': '*',
    'description': validate_descrip(node['<description>']),
    'additionalProperties': False,
    'submittable': node['<submittable>'],
    'validators': None,
    'systemProperties' : sy,
    'links': [],
    'required': ['submitter_id', 'type'],
    "uniqueKeys": d,
    'properties': {} }

    if terms == 't':
        del outdict['nodeTerms']
    return outdict


def properties_builder(node_name, vdictlist, category, omitterms):
    """Constructs the properties dictionary that will be added to the main node dictionary."""
    if category == 'data_file':
        propdict = {'$ref' : S("_definitions.yaml#/data_file_properties")}
    else:
        propdict = {'$ref' : S("_definitions.yaml#/ubiquitous_properties")}

    for n in vdictlist:            
        if n['<node>'] == node_name:
            n['<description>'] = validate_descrip(n['<description>'])
            if omitterms == 't':
                propdict[str(validate_property_name(n['<field>']))] = {
                'description': n['<description>'],
                 'type': stripper(n['<type>']),
                  'enums': enums_builder_noterms(enum_merger(n['<options1>'] + n['<options2>'] + n['<options3>']+  n['<options4>'] +n['<options5>'] + n['<options6>'] + n['<options7>'] + n['<options8>']))
                  }
                if n['<type>'] == 'string':
                    propdict[n['<field>']]['pattern'] = stripper(n['<pattern>'])
                    if propdict[n['<field>']]['pattern'] == None:
                        del propdict[n['<field>']]['pattern']

                if not math.isnan(n['<maximum>']):
                    propdict[n['<field>']]['maximum'] = stripper(int(n['<maximum>']))

                if not math.isnan(n['<minimum>']):
                    propdict[n['<field>']]['minimum'] = stripper(int(n['<minimum>']))


                # if 'project' in links:
                #     propdict[n['<field>']].update({'$ref': })
                
                if n['<type>'] == 'enum':
                    try:    
                        del propdict[n['<field>']]['type']
                    except KeyError:
                        pass
                else:
                    del propdict[n['<field>']]['enums']
            else:
                propdict[str(validate_property_name(n['<field>']))] = {
                    'description': n['<description>'],
                    'terms': get_terms(n['<terms>']),  
                    'type': stripper(n['<type>']),
                    'enumTerms': enums_builder(enum_merger(n['<options1>'] + n['<options2>'] + n['<options3>']+  n['<options4>'] +n['<options5>'] + n['<options6>'] + n['<options7>'] + n['<options8>']))
                    }
                if n['<type>'] == 'string':
                    propdict[n['<field>']]['pattern'] = stripper(n['<pattern>'])
                    if propdict[n['<field>']]['pattern'] == None:
                        del propdict[n['<field>']]['pattern']

                if not math.isnan(n['<maximum>']):
                    propdict[n['<field>']]['maximum'] = stripper(int(n['<maximum>']))

                if not math.isnan(n['<minimum>']):
                    propdict[n['<field>']]['minimum'] = stripper(int(n['<minimum>']))


                # if 'project' in links:
                #     propdict[n['<field>']].update({'$ref': })
                
                if n['<type>'] == 'enum':
                    try:
                        
                        del propdict[n['<field>']]['type']
                    except KeyError:
                        pass
                else:
                    del propdict[n['<field>']]['enumTerms']
    return schema_utils.sortdictionary(propdict)

def properties_preprocessing(vdictlist, ndictlist):
    """Takes in the properties of a node and screens them for illegal values, transforms enums into lists, and finds properties
    labeled as required and adds them to the required key. """

    for n in vdictlist:
        # if isinstance(n['<options>'], str):
        #     n['<options>'] = validatestring(n['<options>'])

        if n['<type>'] == 'enum':
            n['<options1>'] = enum2list(n['<options1>'])
            n['<options2>'] = enum2list(n['<options2>'])
            n['<options3>'] = enum2list(n['<options3>'])
            n['<options4>'] = enum2list(n['<options4>'])
            n['<options5>'] = enum2list(n['<options5>'])
            n['<options6>'] = enum2list(n['<options6>'])
            n['<options7>'] = enum2list(n['<options7>'])
            n['<options8>'] = enum2list(n['<options8>'])

        if n['<required>'] == True:
            node2mod = next(d for d in ndictlist if d['id'] == n['<node>'])
            node2mod['required'].append(n['<field>'])



    

def validate_property_name(string):
    if type(string) != str and math.isnan(string):
        return None
    # match = re.search('''[^a-zA-Z\s0-9'",_/-]''', string)
    match = re.search('''[^a-zA-Z_0-9]''', string)
    if match:
        raise Exception(f"Illegal character {match} found in property name {string}. Only letters and underscore allowed.")
    return string

def validate_node_name(string):
    if type(string) != str:
        if math.isnan(string):
            return None
    match = re.search('''[^a-zA-Z_]''', string)
    if match:
        raise Exception(f"Illegal character {match} found in node name {string}. Only lowercase letters and underscore allowed.")
    return string.lower()

def validatestring(string):
    if type(string) != str and math.isnan(string):
        return None
    # match = re.search('''[^a-zA-Z\s0-9'",_/-]''', string)
    match = re.search('[^ -~]', string)
    
    if match:
        raise Exception(f"Illegal character {match} was found in {string}")

def validate_descrip(string):
    if type(string) != str and math.isnan(string):
        return None
    # S = ruamel.yaml.scalarstring.DoubleQuotedScalarString
    # st = f"""{string}"""
    string = stripper(string)
    return string.replace(':', '-')

def get_terms(terms):
    if isinstance(terms, str):
        lterms = terms.split(',')
        terms = [{'$ref': S(stripper(t))} for t in lterms]
        return terms
    return None

def enums_builder(enums):
    enumdict = {}
    if isinstance(enums, list):
        for e in enums:
            refs = get_enumdefs(e)
            enum = get_enum(e)
            enumdict[enum] = refs
        return enumdict
    return None

def enums_builder_noterms(enums):
    enuml = []
    if isinstance(enums, list):
        for e in enums:
            enum = get_enum(e)
            enuml.append(enum)
        return enuml
    return None
    
def nodeTerms2list(string):
    if type(links) != str and math.isnan(links):
        return None
    strs = string.split(',')
    strs = [{'$ref': stripper(s)} for s in strs]
    return strs

def get_enumdefs(enum):
    if isinstance(enum, str):
        if '{' in enum:
            start = enum.find('{')+1
            end = enum.find('}')
            assert end != -1, f"Closing bracket mismatch in enum {enum}"
                
            refs = stripper(enum[start:end])
            if refs == '':
                return None
            cre = refs.split(',')
            crefs = [stripper(r) for r in cre]
            return [{'$ref': S(r)} for r in crefs]
    

def get_enum(enum):
    if isinstance(enum, str):
        if '{' in enum:
            end = enum.find('{')
            enum = stripper(enum[:end])
            return enum
    return enum


def addlinks(ndict, maindict):
    """Builds a links dictionary template and adds values from the input data. Then merges to the main node dictionary"""

    links = []
    if type(ndict['<link_name>']) != list and math.isnan(ndict['<link_name>']):
        return None
    #Hackish attempt to remove false links
    todel = []
    for i in range(len(ndict['<link_name>'])):
        if ndict['<link_name>'][i] == '':
            todel.append(i)
    for i in todel:
        del ndict['<link_name>'][i]
    for lin in range(len(ndict['<link_name>'])):
        if isinstance(ndict['<link_name>'][lin], str):
            start = lin
            for l in range(start, len(ndict['<link_name>'])):

                link = {'name': stripper(ndict['<link_name>'][l]),
                        'backref': stripper(ndict['<backref>'][l]),
                        'label': stripper(ndict['<label>'][l]),
                        'target_type': stripper(ndict['<target>'][l]),
                        'multiplicity': stripper(ndict['<multiplicity>'][l]),
                        'required': stripper(ndict['<link_required>'][l])}
                links.append(link)

    # if len(ndict['<link_name>'][-1]) > 1:
    #     for l in range(len(ndict['<link_name>'][-1])):
    #         if not isinstance(ndict['<link_name>'][-1][l], list):
    #             link = {'name': stripper(ndict['<link_name>'][-1][l]),
    #                     'backref': stripper(ndict['<backref>'][-1][l]),
    #                     'label': stripper(ndict['<label>'][-1][l]),
    #                     'target_type': stripper(ndict['<target>'][-1][l]),
    #                     'multiplicity': stripper(ndict['<multiplicity>'][-1][l]),
    #                     'required': stripper(ndict['<link_required>'][-1][l])}
    #         links.append(link)
    if not math.isnan(ndict['<link_group_required>']):
        subgroups = []

        #Currently only supports 1 subgroup
        for l in range(len(ndict['<link_name>'][0][0])):
                subgroup = {'name': stripper(ndict['<link_name>'][0][0][l]),
                        'backref': stripper(ndict['<backref>'][0][0][l]),
                        'label': stripper(ndict['<label>'][0][0][l]),
                        'target_type': stripper(ndict['<target>'][0][0][l]),
                        'multiplicity': stripper(ndict['<multiplicity>'][0][0][l]),
                        'required': stripper(ndict['<link_required>'][0][0][l])}
                subgroups.append(subgroup)
        sub = {'exclusive': ndict['<group_exclusive>'], 'required': ndict['<link_group_required>'],  'subgroup': subgroups}
        links.append(sub)
    return links

# def process_subgroups(ndict, maindict, items):
    
    
def links2list(links):
    """Parses the string read in from links input field and transforms it to a list"""
    if type(links) != str and math.isnan(links):
        return None
    outlinks = []
    groups = []
    while '[' in links:
        start = links.find('[')+1
        end = links.find(']')
        group = stripper(links[start:end])
        groups.append(group)
        links = links[end+2:]
        
    for l in groups:
        outlinks.append([links2list(l)])
    
    if isinstance(links, str):
        
        links = links.split(',')
        links = [x.strip() for x in links]
        nongrouplinks = []
        for l in links:
            if l.upper() == 'TRUE':
                # nongrouplinks += True
                nongrouplinks.append(True)
            elif l.upper() == 'FALSE':
                # nongrouplinks += False
                nongrouplinks.append(False)
            else:
                nongrouplinks.append(l)
        # outlinks.append(nongrouplinks)
        outlinks += nongrouplinks
        return outlinks

        # if ',' in links:
        #     return links.split(',')
        
    return [links]

def node_preprocess(ndictlist):
    """Adds the links to the main node links field after being transformed to a list"""

    for n in ndictlist:
        if type(n['<link_name>']) != str and math.isnan(n['<link_name>']):
            continue
        n['<link_name>'] = links2list(n['<link_name>'])
        n['<link_required>'] = links2list(n['<link_required>'])
        n['<backref>'] = links2list(n['<backref>'])
        n['<target>'] = links2list(n['<target>'])
        n['<multiplicity>'] = links2list(n['<multiplicity>'])
        n['<label>'] = links2list(n['<label>'])
        
def enum_merger(lists):
    if isinstance(lists, list):
        return sorted([' '.join(x.split()) for x in lists if str(x) != 'nan'])
    return lists
        


def property_reference_setter(diclinks):
    """Searches the links block and finds the multiplicities for each link. Then puts a reference for each link in the properties
    block"""

    l = diclinks
    if l['name'] == 'project':
        if l['multiplicity'] == 'many_to_one':
            d['properties'].update({'projects': {'$ref':S("_definitions.yaml#/to_many_project") }})
        else:
            d['properties'].update({'projects': {'$ref':S("_definitions.yaml#/to_one_project") }})
    else:
        if l['multiplicity'] == 'many_to_one':
            d['properties'].update({f"{l['name']}": {'$ref':S("_definitions.yaml#/to_many") }})
        else:
            d['properties'].update({f"{l['name']}": {'$ref':S("_definitions.yaml#/to_one") }})

def enum2list(enums):
    """Transforms a string of enums into a list. For values that could be interpreted in yaml as nonstring, it adds quotations"""
    if isinstance(enums, str):

    #    :
            #Enums already are in double quotes. Assumes no missing quotes
        splitenums = enums.split('|')
        final = set()
        clean_enums = [stripper(x) for x in splitenums]
        fenums = list(filter(lambda x: x != '|' and x != '', clean_enums))
        # enumpro = list(filter(lambda x: x != ' ' and x != ',' and x != '' an, splitenums))
        for s in fenums:
            if s.lower() in ['yes', 'no', 'true', 'false'] or isinstance(s, int) or isinstance(s, float):
                final.add(S(s))
            else:
                final.add(s)
        
        return list(final)
        # else:
        #     splitenums = enums.split('|')
        #     stripped = []
        #     final = set()
        #     for s in splitenums:
        #         stripped.append(s.strip())
        #     for s in stripped:
        #         if s.lower() in ['yes', 'no']:
        #             final.add(S(s))
        #         else:
        #             final.add(s)

        #     return list(final)
    # else:
    return [enums]

if __name__ == "__main__":
    args = get_params()
    # Read in the nodes and variables tsvs located in current directory
    # files = glob.glob('./*')
    # nfile = [f for f in files if 'nodes' in f][0]
    # vfile = [f for f in files if 'variables' in f][0]

    nodes = read_csv(args.nodes, index_col=None, header=0, sep = '\t', encoding = 'utf-8')
    variables = read_csv(args.variables, index_col=None, header=0, sep = '\t', encoding = 'utf-8')
    
    # Transform nodes tsv into a dictionary and process fields
    nodedicts = nodes.to_dict('records')
    node_preprocess(nodedicts)

    # Create a properly formatted master dictionary for every node
    dictlist = []
    for r in range(len(nodedicts)):

        dict2add = nodedicts[r]
        dictlist.append(buildnode(dict2add, args.noterms))

    # Add the properly formatted links contents to each dictonary
    linknames = {}
    for i in range(len(dictlist)):
        links =  addlinks(nodedicts[i], dictlist[i])        
        dictlist[i]['links'] = links
        
    
    vdictlist = variables.to_dict('records')
    nodes_to_update = set([n['<node>'] for n in vdictlist])
    nodes_available = [n['id'] for n in dictlist]
    properties_preprocessing(vdictlist, dictlist)

    # Construct and merge the properties fields dictionaries to respective master dictionary
    for node in nodes_to_update:
        assert node in nodes_available, "Must contruct a node before adding properties"
        for n in dictlist:
            if n['id'] == node:
                n['properties'] = properties_builder(node, vdictlist, n['category'], args.noterms)
                if n['category'] == 'data_file':
                    n['required'] += ['file_name', 'file_size', 'data_format', 'md5sum']
    #dump the dictionarys to yaml files
    
    yaml= YAML()
    yaml.default_flow_style = False
    yaml.indent(offset = 2, sequence = 4, mapping = 2)
    def my_represent_none(self, data):
        return self.represent_scalar(u'tag:yaml.org,2002:null', u'null')
    yaml.representer.add_representer(type(None), my_represent_none)
    for d in dictlist:
        index = 0
        has_sub = False
        #Finding a subgroup if it exists
        if d['links'] is None:
            continue
        for key in d['links']:
            dlinks = d['links']
            if 'subgroup' in key.keys():
                # dlinks = d['links'][index]['subgroup']
                has_sub = True
                break
            index += 1

        #Searches grouped links if they exist
        if has_sub:
            for l in d['links'][index]['subgroup']:
                property_reference_setter(l)
        #Searches ungrouped links if they exist
        if index and has_sub:
            for l in d['links'][:-1]:
                property_reference_setter(l)
        #Since a subgroup will be found in last element
        elif index:
            for l in d['links']:
                property_reference_setter(l)
        

        dprop = d['properties']
        del d['properties']
        duniq = d['uniqueKeys']
        del d['uniqueKeys']
        #insert blank lines in node schema
        data = ruamel.yaml.comments.CommentedMap(d)
        data.yaml_set_comment_before_after_key('required', before='\n')
        data.yaml_set_comment_before_after_key('systemProperties', before='\n')
        data.yaml_set_comment_before_after_key('links', before='\n')
        data.yaml_set_comment_before_after_key('uniqueKeys', before='\n')
        data.yaml_set_comment_before_after_key('properties', before='\n')
        data.yaml_set_comment_before_after_key('id', before='\n')
        #insert blank lines in properties
        dataprop = ruamel.yaml.comments.CommentedMap(dprop)
        for k in dprop.keys():
            dataprop.yaml_set_comment_before_after_key(k, before='\n')

        n = d['id']

        # Write up to uniqueKeys
        outpath = args.output + f"{n}.yaml"
        os.makedirs(os.path.dirname(outpath), exist_ok=True)
        fs = open(outpath, 'w')
        yaml.dump(data, fs)
        fs.close()

        #Write uniqueKeys
        yaml= YAML()
        yaml.default_flow_style = None
        yaml.indent(offset = 2, sequence = 4, mapping = 2)
        fs = open(outpath, 'a')
        yaml.dump({'uniqueKeys': duniq}, fs)
        fs.close()
        #Write properties
        
        yaml= YAML()
        yaml.default_flow_style = False
        yaml.indent(offset = 2, sequence = 4, mapping = 2)
        fs = open(outpath, 'a')
        yaml.dump({'properties': dataprop}, fs)
        fs.close()