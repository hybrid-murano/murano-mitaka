#    Copyright (c) 2014 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import eventlet
import six
from yaql.language import specs
from yaql.language import utils
from yaql.language import yaqltypes

from murano.dsl import constants
from murano.dsl import dsl
from murano.dsl import dsl_types
from murano.dsl import helpers
from murano.dsl import reflection


@specs.parameter('object_', dsl.MuranoObjectParameter())
def id_(object_):
    return object_.id


@specs.parameter('object_', dsl.MuranoObjectParameter())
@specs.parameter('type__', dsl.MuranoTypeParameter())
@specs.parameter('version_spec', yaqltypes.String(True))
def cast(context, object_, type__, version_spec=None):
    return helpers.cast(
        object_, type__.type.name,
        version_spec or helpers.get_type(context))


@specs.parameter('__type_name', dsl.MuranoTypeParameter())
@specs.parameter('__extra', utils.MappingType)
@specs.parameter('__owner', dsl.MuranoObjectParameter(
    nullable=True, decorate=False))
@specs.parameter('__object_name', yaqltypes.String(True))
def new(__context, __type_name, __owner=None, __object_name=None, __extra=None,
        **parameters):
    object_store = helpers.get_object_store(__context)
    executor = helpers.get_executor(__context)
    new_context = __context.create_child_context()
    for key, value in six.iteritems(parameters):
        if utils.is_keyword(key):
            new_context[key] = value
    return __type_name.type.new(
        __owner, object_store, executor, name=__object_name)(
        new_context, **parameters)


@specs.parameter('type_name', dsl.MuranoTypeParameter())
@specs.parameter('parameters', utils.MappingType)
@specs.parameter('extra', utils.MappingType)
@specs.parameter('owner', dsl.MuranoObjectParameter(nullable=True))
@specs.parameter('object_name', yaqltypes.String(True))
@specs.name('new')
def new_from_dict(type_name, context, parameters,
                  owner=None, object_name=None, extra=None):
    return new(context, type_name, owner, object_name, extra,
               **utils.filter_parameters_dict(parameters))


@specs.parameter('object_', dsl.MuranoObjectParameter(decorate=False))
@specs.parameter('func', yaqltypes.Lambda())
def super_(context, object_, func=None):
    cast_type = helpers.get_type(context)
    if func is None:
        return [object_.cast(type) for type in cast_type.parents(
            object_.real_this.type)]
    return six.moves.map(func, super_(context, object_))


@specs.parameter('object_', dsl.MuranoObjectParameter(decorate=False))
@specs.parameter('func', yaqltypes.Lambda())
def psuper(context, object_, func=None):
    if func is None:
        return super_(context, object_)
    return helpers.parallel_select(super_(context, object_), func)


@specs.extension_method
def require(value):
    if value is None:
        raise ValueError('Required value is missing')
    return value


@specs.parameter('obj', dsl.MuranoObjectParameter())
@specs.parameter('murano_class_ref', dsl.MuranoTypeParameter())
@specs.extension_method
def find(obj, murano_class_ref):
    return obj.find_owner(murano_class_ref, optional=True)


@specs.parameter('seconds', yaqltypes.Number())
def sleep_(seconds):
    eventlet.sleep(seconds)


@specs.parameter('object_', dsl.MuranoObjectParameter(nullable=True))
def type_(object_):
    return None if object_ is None else object_.type.get_reference()


@specs.name('type')
@specs.parameter('object_', dsl.MuranoObjectParameter(nullable=True))
def type_legacy(object_):
    return None if object_ is None else object_.type.name


@specs.name('type')
@specs.parameter('cls', dsl.MuranoTypeParameter())
def type_from_name(cls):
    return cls


@specs.parameter('object_', dsl.MuranoObjectParameter(nullable=True))
def typeinfo(object_):
    return None if object_ is None else object_.type


@specs.parameter('cls', dsl.MuranoTypeParameter())
@specs.name('typeinfo')
def typeinfo_for_class(cls):
    return cls.type


@specs.parameter('object_', dsl.MuranoObjectParameter(nullable=True))
def name(object_):
    return None if object_ is None else object_.name


@specs.parameter('obj', dsl.MuranoObjectParameter(decorate=False))
@specs.parameter('property_name', yaqltypes.Keyword())
@specs.name('#operator_.')
def obj_attribution(context, obj, property_name):
    return obj.get_property(property_name, context)


@specs.parameter('cls', dsl_types.MuranoTypeReference)
@specs.parameter('property_name', yaqltypes.Keyword())
@specs.name('#operator_.')
def obj_attribution_static(context, cls, property_name):
    return cls.type.get_property(property_name, context)


@specs.parameter('receiver', dsl.MuranoObjectParameter(decorate=False))
@specs.parameter('expr', yaqltypes.Lambda(method=True))
@specs.inject('operator', yaqltypes.Super(with_context=True))
@specs.name('#operator_.')
def op_dot(context, receiver, expr, operator):
    executor = helpers.get_executor(context)
    type_context = executor.context_manager.create_type_context(receiver.type)
    obj_context = executor.context_manager.create_object_context(receiver)
    ctx2 = helpers.link_contexts(
        helpers.link_contexts(context, type_context),
        obj_context)
    return operator(ctx2, receiver, expr)


@specs.parameter('receiver', dsl_types.MuranoTypeReference)
@specs.parameter('expr', yaqltypes.Lambda(method=True))
@specs.inject('operator', yaqltypes.Super(with_context=True))
@specs.name('#operator_.')
def op_dot_static(context, receiver, expr, operator):
    executor = helpers.get_executor(context)
    type_context = executor.context_manager.create_type_context(
        receiver.type)
    ctx2 = helpers.link_contexts(context, type_context)
    return operator(ctx2, receiver, expr)


@specs.parameter('prefix', yaqltypes.Keyword())
@specs.parameter('name', yaqltypes.Keyword())
@specs.name('#operator_:')
def ns_resolve(context, prefix, name):
    return helpers.get_class(prefix + ':' + name, context).get_reference()


@specs.parameter('name', yaqltypes.Keyword())
@specs.name('#unary_operator_:')
def ns_resolve_unary(context, name):
    return ns_resolve(context, '', name)


@specs.parameter('obj', dsl.MuranoObjectParameter(nullable=True))
@specs.parameter('type_', dsl.MuranoTypeParameter())
@specs.name('#operator_is')
def is_instance_of(obj, type_):
    if obj is None:
        return False
    return type_.type.is_compatible(obj)


def register(context, runtime_version):
    context.register_function(cast)
    context.register_function(new)
    context.register_function(new_from_dict)
    context.register_function(id_)
    context.register_function(super_)
    context.register_function(psuper)
    context.register_function(require)
    context.register_function(find)
    context.register_function(sleep_)
    context.register_function(typeinfo)
    context.register_function(typeinfo_for_class)
    context.register_function(name)
    context.register_function(obj_attribution)
    context.register_function(obj_attribution_static)
    context.register_function(op_dot)
    context.register_function(op_dot_static)
    context.register_function(ns_resolve)
    context.register_function(ns_resolve_unary)
    reflection.register(context)
    context.register_function(is_instance_of)
    if runtime_version <= constants.RUNTIME_VERSION_1_3:
        context.register_function(type_legacy)
    else:
        context.register_function(type_)

    if runtime_version <= constants.RUNTIME_VERSION_1_1:
        context = context.create_child_context()
        for t in ('id', 'cast', 'super', 'psuper', 'type'):
            for spec in utils.to_extension_method(t, context):
                context.register_function(spec)

    context.register_function(type_from_name)

    return context
