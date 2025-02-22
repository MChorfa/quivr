from uuid import UUID
from models.databases.repository import Repository

from logger import get_logger

logger = get_logger(__name__)


class Brain(Repository):
    def __init__(self, supabase_client):
        self.db = supabase_client

    def get_user_brains(self, user_id):
        response = (
            self.db.from_("brains_users")
            .select("id:brain_id, brains (id: brain_id, name)")
            .filter("user_id", "eq", user_id)
            .execute()
        )
        return [item["brains"] for item in response.data]

    def get_brain_for_user(self, user_id, brain_id):
        response = (
            self.db.from_("brains_users")
            .select("id:brain_id, rights, brains (id: brain_id, name)")
            .filter("user_id", "eq", user_id)
            .filter("brain_id", "eq", brain_id)
            .execute()
        )
        if len(response.data) == 0:
            return None
        return response.data[0]

    def get_brain_details(self, brain_id):
        response = (
            self.db.from_("brains")
            .select("id:brain_id, name, *")
            .filter("brain_id", "eq", brain_id)
            .execute()
        )
        return response.data

    def delete_brain_user_by_id(self, user_id, brain_id):
        results = (
            self.db.table("brains_users")
            .select("*")
            .match({"brain_id": brain_id, "user_id": user_id, "rights": "Owner"})
            .execute()
        )
        return results

    def delete_brain_vector(self, brain_id: str):
        results = (
            self.db.table("brains_vectors")
            .delete()
            .match({"brain_id": brain_id})
            .execute()
        )

        return results

    def delete_brain_user(self, brain_id: str):
        results = (
            self.db.table("brains_users")
            .delete()
            .match({"brain_id": brain_id})
            .execute()
        )

        return results

    def delete_brain(self, brain_id: str):
        results = (
            self.db.table("brains").delete().match({"brain_id": brain_id}).execute()
        )

        return results

    def create_brain(self, name):
        return self.db.table("brains").insert({"name": name}).execute()

    def create_brain_user(self, user_id: UUID, brain_id, rights, default_brain):
        response = (
            self.db.table("brains_users")
            .insert(
                {
                    "brain_id": str(brain_id),
                    "user_id": str(user_id),
                    "rights": rights,
                    "default_brain": default_brain,
                }
            )
            .execute()
        )

        return response

    def create_brain_vector(self, brain_id, vector_id, file_sha1):
        response = (
            self.db.table("brains_vectors")
            .insert(
                {
                    "brain_id": str(brain_id),
                    "vector_id": str(vector_id),
                    "file_sha1": file_sha1,
                }
            )
            .execute()
        )
        return response.data

    def get_vector_ids_from_file_sha1(self, file_sha1: str):
        # move to vectors class
        vectorsResponse = (
            self.db.table("vectors")
            .select("id")
            .filter("metadata->>file_sha1", "eq", file_sha1)
            .execute()
        )
        return vectorsResponse.data

    def update_brain_fields(self, brain_id, brain_name):
        self.db.table("brains").update({"name": brain_name}).match(
            {"brain_id": brain_id}
        ).execute()

    def get_brain_vector_ids(self, brain_id):
        """
        Retrieve unique brain data (i.e. uploaded files and crawled websites).
        """

        response = (
            self.db.from_("brains_vectors")
            .select("vector_id")
            .filter("brain_id", "eq", brain_id)
            .execute()
        )

        vector_ids = [item["vector_id"] for item in response.data]

        if len(vector_ids) == 0:
            return []

        return vector_ids

    def delete_file_from_brain(self, brain_id, file_name: str):
        # First, get the vector_ids associated with the file_name
        vector_response = (
            self.db.table("vectors")
            .select("id")
            .filter("metadata->>file_name", "eq", file_name)
            .execute()
        )
        vector_ids = [item["id"] for item in vector_response.data]

        # For each vector_id, delete the corresponding entry from the 'brains_vectors' table
        for vector_id in vector_ids:
            self.db.table("brains_vectors").delete().filter(
                "vector_id", "eq", vector_id
            ).filter("brain_id", "eq", brain_id).execute()

            # Check if the vector is still associated with any other brains
            associated_brains_response = (
                self.db.table("brains_vectors")
                .select("brain_id")
                .filter("vector_id", "eq", vector_id)
                .execute()
            )
            associated_brains = [
                item["brain_id"] for item in associated_brains_response.data
            ]

            # If the vector is not associated with any other brains, delete it from 'vectors' table
            if not associated_brains:
                self.db.table("vectors").delete().filter(
                    "id", "eq", vector_id
                ).execute()

        return {"message": f"File {file_name} in brain {brain_id} has been deleted."}

    def get_default_user_brain_id(self, user_id: UUID):
        response = (
            self.db.from_("brains_users")
            .select("brain_id")
            .filter("user_id", "eq", user_id)
            .filter("default_brain", "eq", True)
            .execute()
        )

        return response

    def get_brain_by_id(self, brain_id: UUID):
        response = (
            self.db.from_("brains")
            .select("id:brain_id, name, *")
            .filter("brain_id", "eq", brain_id)
            .execute()
        )

        return response
