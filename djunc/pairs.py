from djunc import projectors, qs


def field(name):
    return qs.include_fields(name), projectors.field(name)


def unzip(pairs):
    prepare_fns, project_fns = zip(*pairs)
    return qs.pipe(*prepare_fns), projectors.compose(*project_fns)


"""
Below are functions which return pairs that use `prefetch_related` to efficiently load
related objects, and then project those related objects. We use `prefetch_related` to
load all relationship types because this means our functions can be recursive - we
can apply pairs to the related querysets, all the way down the tree.

There are six types of relationship from the point of view of the "main" object:

  * Forward one-to-one - a OneToOneField on the main object
  * Reverse one-to-one - a OneToOneField on the related object
  * Forward many-to-one - a ForeignKey on the main object
  * Reverse many-to-one - a ForeignKey on the related object
  * Forward many-to-many - a ManyToManyField on the main object
  * Reverse many-to-many - a ManyToManyField on the related object

ManyToManyFields are symmetrical, so the latter two collapse down to the same thing.
The forward one-to-one and many-to-one are identical as they both relate a single
related object to the main object. The reverse one-to-one and many-to-one are identical
except the former relates the main object to a single related object, and the latter
relates the main object to many related objects.

There is a function for manually specifying each of these relationship types, and then
an `auto_relationship` function which selects the correct one by introspecting the
relationships.
"""


def _forward_relationship(name, related_queryset, relationship_pair):
    prepare_related_queryset, project_relationship = relationship_pair
    related_queryset = prepare_related_queryset(related_queryset)
    queryset_function = qs.prefetch_forward_relationship(name, related_queryset)
    projector = projectors.relationship(name, project_relationship, many=False)
    return queryset_function, projector


def _make_reverse_relationship(many):
    def reverse_relationship(name, related_name, related_queryset, relationship_pair):
        prepare_related_queryset, project_relationship = relationship_pair
        related_queryset = prepare_related_queryset(related_queryset)
        queryset_function = qs.prefetch_reverse_relationship(
            name, related_name, related_queryset
        )
        projector = projectors.relationship(name, project_relationship, many=many)
        return queryset_function, projector

    return reverse_relationship


forward_one_to_one_relationship = _forward_relationship
forward_many_to_one_relationship = _forward_relationship
reverse_one_to_one_relationship = _make_reverse_relationship(many=False)
reverse_many_to_one_relationship = _make_reverse_relationship(many=True)


def many_to_many_relationship(name, related_queryset, relationship_pair):
    prepare_related_queryset, project_relationship = relationship_pair
    related_queryset = prepare_related_queryset(related_queryset)
    queryset_function = qs.prefetch_many_to_many_relationship(name, related_queryset)
    projector = projectors.relationship(name, project_relationship, many=True)
    return queryset_function, projector
