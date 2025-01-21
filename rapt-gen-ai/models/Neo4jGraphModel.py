from neo4j import GraphDatabase
import numpy as np

class Neo4jDatabase:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def insert_triple(self, head, relation, tail, head_embedding, tail_embedding):
        with self.driver.session() as session:
            session.write_transaction(self._insert_triple, head, relation, tail, head_embedding, tail_embedding)

    @staticmethod
    def _insert_triple(tx, head, relation, tail, head_embedding, tail_embedding):
        query = """
        MERGE (h:Entity {name: $head})
        SET h.embedding = $head_embedding
        MERGE (t:Entity {name: $tail})
        SET t.embedding = $tail_embedding
        MERGE (h)-[:$relation]->(t)
        """
        tx.run(query, head=head, relation=relation, tail=tail, head_embedding=head_embedding, tail_embedding=tail_embedding)

    def delete_entity(self, entity_name):
        with self.driver.session() as session:
            session.write_transaction(self._delete_entity, entity_name)

    @staticmethod
    def _delete_entity(tx, entity_name):
        query = """
        MATCH (e:Entity {name: $entity_name})
        DETACH DELETE e
        """
        tx.run(query, entity_name=entity_name)

    def delete_relation(self, head, relation, tail):
        with self.driver.session() as session:
            session.write_transaction(self._delete_relation, head, relation, tail)

    @staticmethod
    def _delete_relation(tx, head, relation, tail):
        query = """
        MATCH (h:Entity {name: $head})-[r:$relation]->(t:Entity {name: $tail})
        DELETE r
        """
        tx.run(query, head=head, relation=relation, tail=tail)

    def retrieve_entity_with_relations(self, entity_name, related_entity_name=None, relation_type=None):
        with self.driver.session() as session:
            return session.read_transaction(self._retrieve_entity_with_relations, entity_name, related_entity_name, relation_type)

    @staticmethod
    def _retrieve_entity_with_relations(tx, entity_name, related_entity_name, relation_type):
        query = """
        MATCH (e:Entity {name: $entity_name})-[r]->(related)
        WHERE ($related_entity_name IS NULL OR related.name = $related_entity_name)
          AND ($relation_type IS NULL OR type(r) = $relation_type)
        RETURN e, r, related
        """
        result = tx.run(query, entity_name=entity_name, related_entity_name=related_entity_name, relation_type=relation_type)
        return [record.data() for record in result]

    def list_all_nodes(self):
        with self.driver.session() as session:
            return session.read_transaction(self._list_all_nodes)

    @staticmethod
    def _list_all_nodes(tx):
        query = """
        MATCH (n)
        RETURN n.name AS name, labels(n) AS labels
        """
        result = tx.run(query)
        return [record.data() for record in result]

    def list_all_relationships(self):
        with self.driver.session() as session:
            return session.read_transaction(self._list_all_relationships)

    @staticmethod
    def _list_all_relationships(tx):
        query = """
        MATCH (n)-[r]->(m)
        RETURN n.name AS start, type(r) AS relation, m.name AS end
        """
        result = tx.run(query)
        return [record.data() for record in result]

    def wipe_database(self):
        with self.driver.session() as session:
            session.write_transaction(self._wipe_database)

    @staticmethod
    def _wipe_database(tx):
        query = """
        MATCH (n)
        DETACH DELETE n
        """
        tx.run(query)

    def create_vector_index(self, label, property_name):
        with self.driver.session() as session:
            session.write_transaction(self._create_vector_index, label, property_name)

    @staticmethod
    def _create_vector_index(tx, label, property_name):
        query = f"CREATE INDEX IF NOT EXISTS FOR (n:{label}) ON (n.{property_name})"
        tx.run(query)

    def search_by_embedding_similarity(self, label, embedding, top_k=5):
        with self.driver.session() as session:
            return session.read_transaction(self._search_by_embedding_similarity, label, embedding, top_k)

    @staticmethod
    def _search_by_embedding_similarity(tx, label, embedding, top_k):
        query = """
        MATCH (n:{label})
        WHERE n.embedding IS NOT NULL
        WITH n, gds.similarity.cosine(n.embedding, $embedding) AS similarity
        RETURN n.name AS name, similarity
        ORDER BY similarity DESC
        LIMIT $top_k
        """
        result = tx.run(query, embedding=embedding, top_k=top_k)
        return [record.data() for record in result]
