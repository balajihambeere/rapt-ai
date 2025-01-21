from neo4j import GraphDatabase
from neo4j import GraphDatabase, basic_auth
from neo4j.auth_management import AuthManagers
import os

# Replace with your Neo4j Aura credentials
uri = os.environ.get('NEO4J_AURA_URI')
pw = os.environ.get('NEO4J_AURA_PW')


class Neo4jGraph:
    def __init__(self, uri, pw):
        """
        Initialize the Neo4jGraph with a connection to the Neo4j Aura database.
        """
        auth = ("neo4j", pw)
        self.driver = GraphDatabase.driver(uri, auth=AuthManagers.static(auth))

    def close(self):
        """
        Close the connection to the database.
        """
        self.driver.close()

    def generate_embedding(self, text):
        """
        Generate an embedding for the given text using OpenAI API.

        :param text: The text to generate the embedding for.
        :return: A list of floats representing the embedding.
        """
        return client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        ).data[0].embedding

    def insert_triplet(self, triplet):
        """
        Insert a triplet (head, relation, tail) with properties and embeddings.
        Ensure that all nodes have the "Entity" label. If nodes already exist (based on 'name'), they will not be recreated.

        :param triplet: A dictionary containing:
                        - 'head': name of the head node
                        - 'type': type of the relationship
                        - 'tail': name of the tail node
                        - 'head_label' (optional): label for the head node
                        - 'tail_label' (optional): label for the tail node
                        - 'head_properties' (optional): properties for the head node
                        - 'tail_properties' (optional): properties for the tail node
                        - 'relation_properties' (optional): properties for the relationship
        """
        head_name = triplet['head']
        tail_name = triplet['tail']
        relation_type = triplet['type']

        # Ensure that the Entity label is added to all nodes
        head_label = 'Entity' + \
            (':' + triplet.get('head_label', '')
             if triplet.get('head_label') else '')
        tail_label = 'Entity' + \
            (':' + triplet.get('tail_label', '')
             if triplet.get('tail_label') else '')

        head_properties = triplet.get('head_properties', {})
        tail_properties = triplet.get('tail_properties', {})
        relation_properties = triplet.get('relation_properties', {})
        # Store the relation type as a property
        relation_properties['type'] = relation_type

        # Ensure 'name' is included in properties
        head_properties['name'] = head_name
        tail_properties['name'] = tail_name

        # Generate embeddings for head and tail
        head_embedding = self.generate_embedding(head_name)
        tail_embedding = self.generate_embedding(tail_name)

        # Add the embedding as a property
        head_properties['embedding'] = head_embedding
        tail_properties['embedding'] = tail_embedding

        query = """
        MERGE (h:{head_label} {{name: $head_name}})
        SET h += $head_properties
        MERGE (t:{tail_label} {{name: $tail_name}})
        SET t += $tail_properties
        MERGE (h)-[r:RELATION]->(t)
        SET r += $relation_properties
        RETURN h, r, t
        """.format(head_label=head_label, tail_label=tail_label)

        with self.driver.session() as session:
            session.run(
                query,
                head_name=head_name,
                tail_name=tail_name,
                head_properties=head_properties,
                tail_properties=tail_properties,
                relation_properties=relation_properties
            )
        print(f"Inserted triplet with embeddings for {
              head_name} and {tail_name}, both labeled as 'Entity'.")

    def delete_entity(self, name):
        query = """
        MATCH (n {name: $name})
        DETACH DELETE n
        """
        with self.driver.session() as session:
            session.run(query, name=name)

    def delete_relation(self, head_name, tail_name, relation_type):
        """
        Delete a relationship between two nodes based on 'name' and relationship type.

        :param head_name: The 'name' property of the head/start node
        :param tail_name: The 'name' property of the tail/end node
        :param relation_type: The 'type' property of the relationship to delete
        """
        query = """
        MATCH (h {{name: $head_name}})-[r:RELATION {{type: $relation_type}}]->(t {{name: $tail_name}})
        DELETE r
        """

        with self.driver.session() as session:
            session.run(
                query,
                head_name=head_name,
                tail_name=tail_name,
                relation_type=relation_type
            )

    def get_entity_with_relations(self, name, related_names=None, relation_types=None, verbose=False):
        """
        Get an entity and its relationships, optionally filtering by related node names and relationship types.

        :param name: The 'name' property of the node to retrieve
        :param related_names: A list of 'name' properties of related nodes to filter by
        :param relation_types: A list of relationship 'type' properties to filter by
        :return: A list of dictionaries representing the relationships
        """
        # Start building the query
        query = """
        MATCH (n {name: $name})-[r]->(related)
        """
        # Add conditions based on optional parameters
        conditions = []
        if related_names:
            conditions.append("related.name IN $related_names")
        if relation_types:
            conditions.append("r.type IN $relation_types")
        if conditions:
            query += "WHERE " + " AND ".join(conditions) + "\n"
        query += "RETURN n, r, related"

        query += """\n
        UNION
        MATCH (n)-[r]->(related {name: $name})
        """
        # Add conditions based on optional parameters
        conditions = []
        if related_names:
            conditions.append("related.name IN $related_names")
        if relation_types:
            conditions.append("r.type IN $relation_types")
        if conditions:
            query += "WHERE " + " AND ".join(conditions) + "\n"
        query += "RETURN n, r, related"

        # Prepare parameters
        parameters = {'name': name}
        if related_names:
            parameters['related_names'] = related_names
        if relation_types:
            parameters['relation_types'] = relation_types

        if verbose:
            print(query)

        # Execute the query
        with self.driver.session() as session:
            result = session.run(query, **parameters)
            records = list(result)

            if not records:
                raise ValueError(
                    f"Entity '{name}' not found or no relationships matching the criteria.")

            return [{
                'head': record['n']['name'],
                'relation': record['r']['type'],
                'tail': record['related']['name']
            } for record in records]

    def list_all_nodes(self):
        """
        List all nodes in the database.

        :return: A list of node dictionaries.
        """
        query = """
        MATCH (n)
        WITH n, apoc.map.removeKey(properties(n), 'embedding') AS props
        RETURN props
        """
        with self.driver.session() as session:
            result = session.run(query)
            nodes = [record["props"] for record in result]
            return nodes

    def list_all_relationships(self):
        """
        List all relationships in the database.

        :return: A list of relationship dictionaries.
        """
        query = "MATCH ()-[r]->() RETURN r"
        with self.driver.session() as session:
            result = session.run(query)
            relationships = [record["r"] for record in result]
            return relationships

    def wipe_db(self):
        """
        Wipe the entire database.
        """
        query = "MATCH (n) DETACH DELETE n"
        with self.driver.session() as session:
            session.run(query)

    def create_vector_index(self, label, property_name, dimensions):
        """
        Create a vector index for nodes with a specific label and property.

        :param label: The label of the nodes to create the index for.
        :param property_name: The property of the nodes containing the vector data.
        :param dimensions: The number of dimensions of the vector.
        """
        query = f"""
        CREATE VECTOR INDEX vector_index_{property_name} IF NOT EXISTS
        FOR (n:{label})
        ON (n.{property_name})
        OPTIONS {{
            indexConfig: {{
                `vector.dimensions`: {dimensions},
                `vector.similarity_function`: 'cosine'
            }}
        }}
        """
        with self.driver.session() as session:
            session.run(query)
        print(f"Vector index created for label '{label}' on property '{
              property_name}' with {dimensions} dimensions.")

    def search_by_embedding(self, text, top_k=5):
        """
        Search for nodes with embeddings closest to the given embedding, using cosine similarity.

        :param label: The label of the nodes to search for.
        :param property_name: The property where the embedding is stored.
        :param embedding: The vector embedding to search with.
        :param top_k: Number of nearest nodes to return.
        :return: A list of nodes with their similarity scores.
        """
        label = 'Entity'
        property_name = 'embedding'
        embedding = self.generate_embedding(text)
        query = f"""
        CALL db.index.vector.queryNodes('vector_index_{property_name}', $top_k, $embedding)
        YIELD node, score
        RETURN node, score
        ORDER BY score DESC
        LIMIT $top_k
        """
        with self.driver.session() as session:
            result = session.run(query, embedding=embedding, top_k=top_k)
            nodes = [{'node': record['node'], 'score': record['score']}
                     for record in result]
            return nodes
