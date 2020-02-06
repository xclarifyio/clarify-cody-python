

def get_item_hrefs(result_collection):
    """
    Given a result_collection (returned by a previous API call that
    returns a collection, like get_bundle_list() or search()), return a
    list of item hrefs.
    'result_collection' a JSON object returned by a previous API
    call.
    Returns a list, which may be empty if no items were found.
    """

    # Argument error checking.
    assert result_collection is not None

    result = []

    links = result_collection.get('_links')
    if links is not None:
        items = links.get('items')
        if items is not None:
            for item in items:
                result.append(item.get('href'))

    return result


def get_link_href(result_object, link_relation):
    """
    Given a result_object (returned by a previous API call), return
    the link href for a link relation.
    'result_object' a JSON object returned by a previous API call. May not
    be None.
    'link_relation' the link relation for which href is required.
    Returns None if the link does not exist.
    """

    # Argument error checking.
    assert result_object is not None

    result = None

    link = result_object['_links'].get(link_relation)
    if link:
        result = link.get('href')

    return result


def get_embedded(result_object, link_relation):
    """
    Given a result_object (returned by a previous API call), return
    the embedded object for link_relation.  The returned object can be
    treated as a result object in its own right.

    'result_object' a JSON object returned by a previous API call.
    The link relation of the embedded object must have been specified
    when the result_object was originally requested. May not be None.
    'link_relation' the link relation for which href is required. May
    not be None.
    Returns None if the embedded object does not exist.
    """

    # Argument error checking.
    assert result_object is not None
    assert link_relation is not None

    result = None

    embedded_object = result_object.get('_embedded')
    if embedded_object:
        result = embedded_object.get(link_relation)

    return result
