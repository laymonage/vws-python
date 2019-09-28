"""
Tools for managing result codes.
"""

import json

from requests import Response

from vws.exceptions import (
    AuthenticationFailure,
    BadImage,
    Fail,
    ImageTooLarge,
    MetadataTooLarge,
    ProjectInactive,
    RequestTimeTooSkewed,
    TargetNameExist,
    TargetStatusNotSuccess,
    TargetStatusProcessing,
    UnknownTarget,
    UnknownVWSErrorPossiblyBadName,
)


def raise_for_result_code(
    response: Response,
    expected_result_code: str,
) -> None:
    """
    Raise an appropriate exception if the expected result code for a successful
    request is not returned.

    Args:
        response: A response from Vuforia.
        expected_result_code: See
            https://library.vuforia.com/articles/Solution/How-To-Use-the-Vuforia-Web-Services-API.html#How-To-Interperete-VWS-API-Result-Codes
    """
    try:
        result_code = response.json()['result_code']
    except json.decoder.JSONDecodeError as exc:
        assert 'Oops' in response.text
        raise UnknownVWSErrorPossiblyBadName() from exc

    if result_code == expected_result_code:
        return

    exception = {
        'AuthenticationFailure': AuthenticationFailure,
        'BadImage': BadImage,
        'Fail': Fail,
        'ImageTooLarge': ImageTooLarge,
        'InactiveProject': ProjectInactive,
        'MetadataTooLarge': MetadataTooLarge,
        'ProjectInactive': ProjectInactive,
        'RequestTimeTooSkewed': RequestTimeTooSkewed,
        'TargetNameExist': TargetNameExist,
        'TargetStatusNotSuccess': TargetStatusNotSuccess,
        'TargetStatusProcessing': TargetStatusProcessing,
        'UnknownTarget': UnknownTarget,
    }[result_code]

    raise exception(response=response)
