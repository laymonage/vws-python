"""
Tests for helper functions for managing a Vuforia database.
"""

import base64
import io
import random
import uuid
from typing import Optional

import pytest
from mock_vws import MockVWS
from mock_vws.database import VuforiaDatabase

from vws import VWS, CloudRecoService
from vws.exceptions import TargetProcessingTimeout


class TestAddTarget:
    """
    Tests for adding a target.
    """

    @pytest.mark.parametrize('application_metadata', [None, b'a'])
    @pytest.mark.parametrize('active_flag', [True, False])
    def test_add_target(
        self,
        vws_client: VWS,
        high_quality_image: io.BytesIO,
        active_flag: bool,
        application_metadata: Optional[bytes],
        cloud_reco_client: CloudRecoService,
    ) -> None:
        """
        No exception is raised when adding one target.
        """
        name = 'x'
        width = 1
        if application_metadata is None:
            encoded_metadata = None
        else:
            encoded_metadata_bytes = base64.b64encode(application_metadata)
            encoded_metadata = encoded_metadata_bytes.decode('utf-8')

        target_id = vws_client.add_target(
            name=name,
            width=width,
            image=high_quality_image,
            application_metadata=encoded_metadata,
            active_flag=active_flag,
        )
        target_record = vws_client.get_target_record(target_id=target_id)
        assert target_record['name'] == name
        assert target_record['width'] == width
        assert target_record['active_flag'] is active_flag
        vws_client.wait_for_target_processed(target_id=target_id)
        matching_targets = cloud_reco_client.query(image=high_quality_image)
        if active_flag:
            [matching_target] = matching_targets
            assert matching_target['target_id'] == target_id
            query_target_data = matching_target['target_data']
            query_metadata = query_target_data['application_metadata']
            assert query_metadata == encoded_metadata
        else:
            assert matching_targets == []

    def test_add_two_targets(
        self,
        vws_client: VWS,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        No exception is raised when adding two targets with different names.

        This demonstrates that the image seek position is not changed.
        """
        for name in ('a', 'b'):
            vws_client.add_target(
                name=name,
                width=1,
                image=high_quality_image,
                active_flag=True,
                application_metadata=None,
            )


class TestCustomBaseVWSURL:
    """
    Tests for using a custom base VWS URL.
    """

    def test_custom_base_url(self, high_quality_image: io.BytesIO) -> None:
        """
        It is possible to use add a target to a database under a custom VWS
        URL.
        """
        base_vws_url = 'http://example.com'
        with MockVWS(base_vws_url=base_vws_url) as mock:
            database = VuforiaDatabase()
            mock.add_database(database=database)
            vws_client = VWS(
                server_access_key=database.server_access_key,
                server_secret_key=database.server_secret_key,
                base_vws_url=base_vws_url,
            )

            vws_client.add_target(
                name='x',
                width=1,
                image=high_quality_image,
                active_flag=True,
                application_metadata=None,
            )


class TestListTargets:
    """
    Tests for listing targets.
    """

    def test_list_targets(
        self,
        vws_client: VWS,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        It is possible to get a list of target IDs.
        """
        id_1 = vws_client.add_target(
            name='x',
            width=1,
            image=high_quality_image,
            active_flag=True,
            application_metadata=None,
        )
        id_2 = vws_client.add_target(
            name='a',
            width=1,
            image=high_quality_image,
            active_flag=True,
            application_metadata=None,
        )
        assert sorted(vws_client.list_targets()) == sorted([id_1, id_2])


class TestDelete:
    """
    Test for deleting a target.
    """

    def test_delete_target(
        self,
        vws_client: VWS,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        It is possible to delete a target.
        """
        target_id = vws_client.add_target(
            name='x',
            width=1,
            image=high_quality_image,
            active_flag=True,
            application_metadata=None,
        )

        vws_client.wait_for_target_processed(target_id=target_id)
        assert target_id in vws_client.list_targets()
        vws_client.delete_target(target_id=target_id)
        assert target_id not in vws_client.list_targets()


class TestGetTargetSummaryReport:
    """
    Tests for getting a summary report for a target.
    """

    def test_get_target_summary_report(
        self,
        vws_client: VWS,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        Details of a target are returned by ``get_target_summary_report``.
        """
        target_id = vws_client.add_target(
            name='x',
            width=1,
            image=high_quality_image,
            active_flag=True,
            application_metadata=None,
        )

        result = vws_client.get_target_summary_report(target_id=target_id)
        expected_keys = {
            'status',
            'result_code',
            'transaction_id',
            'database_name',
            'target_name',
            'upload_date',
            'active_flag',
            'tracking_rating',
            'total_recos',
            'current_month_recos',
            'previous_month_recos',
        }
        assert set(result.keys()) == expected_keys


class TestGetDatabaseSummaryReport:
    """
    Tests for getting a summary report for a database.
    """

    def test_get_target(self, vws_client: VWS) -> None:
        """
        Details of a database are returned by ``get_database_summary_report``.
        """
        report = vws_client.get_database_summary_report()
        expected_keys = {
            'active_images',
            'current_month_recos',
            'failed_images',
            'inactive_images',
            'name',
            'previous_month_recos',
            'processing_images',
            'reco_threshold',
            'request_quota',
            'request_usage',
            'result_code',
            'target_quota',
            'total_recos',
            'transaction_id',
        }
        assert set(report.keys()) == expected_keys


class TestGetTargetRecord:
    """
    Tests for getting a record of a target.
    """

    def test_get_target_record(
        self,
        vws_client: VWS,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        Details of a target are returned by ``get_target_record``.
        """
        target_id = vws_client.add_target(
            name='x',
            width=1,
            image=high_quality_image,
            active_flag=True,
            application_metadata=None,
        )

        result = vws_client.get_target_record(target_id=target_id)

        expected_keys = {
            'target_id',
            'active_flag',
            'name',
            'width',
            'tracking_rating',
            'reco_rating',
        }
        assert set(result.keys()) == expected_keys


class TestWaitForTargetProcessed:
    """
    Tests for waiting for a target to be processed.
    """

    def test_wait_for_target_processed(
        self,
        vws_client: VWS,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        It is possible to wait until a target is processed.
        """
        target_id = vws_client.add_target(
            name='x',
            width=1,
            image=high_quality_image,
            active_flag=True,
            application_metadata=None,
        )
        report = vws_client.get_target_summary_report(target_id=target_id)
        assert report['status'] == 'processing'
        vws_client.wait_for_target_processed(target_id=target_id)
        report = vws_client.get_target_summary_report(target_id=target_id)
        assert report['status'] != 'processing'

    def test_default_seconds_between_requests(
        self,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        By default, 0.2 seconds are waited between polling requests.
        """
        with MockVWS(processing_time_seconds=0.5) as mock:
            database = VuforiaDatabase()
            mock.add_database(database=database)
            vws_client = VWS(
                server_access_key=database.server_access_key,
                server_secret_key=database.server_secret_key,
            )

            target_id = vws_client.add_target(
                name='x',
                width=1,
                image=high_quality_image,
                active_flag=True,
                application_metadata=None,
            )

            vws_client.wait_for_target_processed(target_id=target_id)
            report = vws_client.get_database_summary_report()
            expected_requests = (
                # Add target request
                1 +
                # Database summary request
                1 +
                # Initial request
                1 +
                # Request after 0.2 seconds - not processed
                1 +
                # Request after 0.4 seconds - not processed
                # This assumes that there is less than 0.1 seconds taken
                # between the start of the target processing and the start of
                # waiting for the target to be processed.
                1 +
                # Request after 0.6 seconds - processed
                1
            )
            # At the time of writing there is a bug which prevents request
            # usage from being tracked so we cannot track this.
            expected_requests = 0
            assert report['request_usage'] == expected_requests

    def test_custom_seconds_between_requests(
        self,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        It is possible to customize the time waited between polling requests.
        """
        with MockVWS(processing_time_seconds=0.5) as mock:
            database = VuforiaDatabase()
            mock.add_database(database=database)
            vws_client = VWS(
                server_access_key=database.server_access_key,
                server_secret_key=database.server_secret_key,
            )

            target_id = vws_client.add_target(
                name='x',
                width=1,
                image=high_quality_image,
                active_flag=True,
                application_metadata=None,
            )

            vws_client.wait_for_target_processed(
                target_id=target_id,
                seconds_between_requests=0.3,
            )
            report = vws_client.get_database_summary_report()
            expected_requests = (
                # Add target request
                1 +
                # Database summary request
                1 +
                # Initial request
                1 +
                # Request after 0.3 seconds - not processed
                # This assumes that there is less than 0.2 seconds taken
                # between the start of the target processing and the start of
                # waiting for the target to be processed.
                1 +
                # Request after 0.6 seconds - processed
                1
            )
            # At the time of writing there is a bug which prevents request
            # usage from being tracked so we cannot track this.
            expected_requests = 0
            assert report['request_usage'] == expected_requests

    def test_custom_timeout(
        self,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        It is possible to set a maximum timeout.
        """
        with MockVWS(processing_time_seconds=0.5) as mock:
            database = VuforiaDatabase()
            mock.add_database(database=database)
            vws_client = VWS(
                server_access_key=database.server_access_key,
                server_secret_key=database.server_secret_key,
            )

            target_id = vws_client.add_target(
                name='x',
                width=1,
                image=high_quality_image,
                active_flag=True,
                application_metadata=None,
            )

            report = vws_client.get_target_summary_report(target_id=target_id)
            assert report['status'] == 'processing'
            with pytest.raises(TargetProcessingTimeout):
                vws_client.wait_for_target_processed(
                    target_id=target_id,
                    timeout_seconds=0.1,
                )

            vws_client.wait_for_target_processed(
                target_id=target_id,
                timeout_seconds=0.5,
            )
            report = vws_client.get_target_summary_report(target_id=target_id)
            assert report['status'] != 'processing'


class TestGetDuplicateTargets:
    """
    Tests for getting duplicate targets.
    """

    def test_get_duplicate_targets(
        self,
        vws_client: VWS,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        It is possible to get the IDs of similar targets.
        """
        target_id = vws_client.add_target(
            name='x',
            width=1,
            image=high_quality_image,
            active_flag=True,
            application_metadata=None,
        )
        similar_target_id = vws_client.add_target(
            name='a',
            width=1,
            image=high_quality_image,
            active_flag=True,
            application_metadata=None,
        )

        vws_client.wait_for_target_processed(target_id=target_id)
        vws_client.wait_for_target_processed(target_id=similar_target_id)
        duplicates = vws_client.get_duplicate_targets(target_id=target_id)
        assert duplicates == [similar_target_id]


class TestUpdateTarget:
    """
    Tests for updating a target.
    """

    def test_update_target(
        self,
        vws_client: VWS,
        high_quality_image: io.BytesIO,
        different_high_quality_image: io.BytesIO,
        cloud_reco_client: CloudRecoService,
    ) -> None:
        """
        It is possible to update a target.
        """
        old_name = uuid.uuid4().hex
        old_width = random.uniform(a=0.01, b=50)
        target_id = vws_client.add_target(
            name=old_name,
            width=old_width,
            image=high_quality_image,
            active_flag=True,
            application_metadata=None,
        )
        vws_client.wait_for_target_processed(target_id=target_id)
        report = vws_client.get_target_summary_report(target_id=target_id)
        [matching_target] = cloud_reco_client.query(image=high_quality_image)
        assert matching_target['target_id'] == target_id
        query_target_data = matching_target['target_data']
        query_metadata = query_target_data['application_metadata']
        assert query_metadata is None

        new_name = uuid.uuid4().hex
        new_width = random.uniform(a=0.01, b=50)
        new_application_metadata = base64.b64encode(b'a').decode('ascii')
        vws_client.update_target(
            target_id=target_id,
            name=new_name,
            width=new_width,
            active_flag=True,
            image=different_high_quality_image,
            application_metadata=new_application_metadata,
        )

        vws_client.wait_for_target_processed(target_id=target_id)
        [matching_target
         ] = cloud_reco_client.query(image=different_high_quality_image, )
        assert matching_target['target_id'] == target_id
        query_target_data = matching_target['target_data']
        query_metadata = query_target_data['application_metadata']
        assert query_metadata == new_application_metadata

        vws_client.update_target(
            target_id=target_id,
            active_flag=False,
        )

        target_details = vws_client.get_target_record(target_id=target_id)
        assert target_details['name'] == new_name
        assert target_details['width'] == new_width
        assert not target_details['active_flag']

    def test_no_fields_given(
        self,
        vws_client: VWS,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        It is possible to give no update fields.
        """
        target_id = vws_client.add_target(
            name='x',
            width=1,
            image=high_quality_image,
            active_flag=True,
            application_metadata=None,
        )
        vws_client.wait_for_target_processed(target_id=target_id)
        vws_client.update_target(target_id=target_id)
