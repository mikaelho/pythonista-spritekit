import ui
from objc_util import *
from objc_util import ObjCInstanceMethodProxy
from scene import Rect, Size

def py_to_cg(value):
  if type(value) == Size:
    w, h = value
    return CGSize(w, h)
  elif len(value) == 4:
    x, y, w, h = value
    return CGRect(CGPoint(x, y), CGSize(w,h))
  elif len(value) == 2:
    x, y = value
    return CGPoint(x, y)
    
def cg_to_py(value):
  if type(value) == ObjCInstanceMethodProxy:
    value = value()
  if type(value) == CGPoint:
    return ui.Point(value.x, value.y)
  elif type(value) == CGVector:
    return ui.Point(value.dx, value.dy)
  elif type(value) == CGRect:
    return Rect(
      value.origin.x, value.origin.y,
      value.size.width, value.size.height)
  elif type(value) == CGSize:
    return Size(value.width, value.height)

def prop(func):
  return property(func, func)
  
def method_or_not(value):
  return value() if type(value) == ObjCInstanceMethodProxy else value
  
def node_relay(attribute_name):
  '''Property creator for pass-through physics properties'''
  p = property(
    lambda self:
      method_or_not(getattr(self.node, attribute_name)),
    lambda self, value:
      setattr(self.node, attribute_name, value)
  )
  return p
  
'''
def node_relay_prop(attribute_name):
  p = property(
    lambda self:
      getattr(self.node, attribute_name)(),
    lambda self, value:
      setattr(self.node, attribute_name, value)
  )
  return p
'''
  
def node_relay_set(attribute_name):
  '''Property creator for pass-through physics properties'''
  set_name = 'set'+attribute_name[0].upper()+attribute_name[1:]+'_'
  p = property(
    lambda self:
      getattr(self.node, attribute_name)(),
    lambda self, value:
      getattr(self.node, set_name)(value)
  )
  return p
  
def convert_relay(attribute_name):
  '''Property creator for pass-through physics properties'''
  p = property(
    lambda self:
      cg_to_py(getattr(self.node, attribute_name)),
    lambda self, value:
      setattr(self.node, attribute_name, py_to_cg(value))
  )
  return p
  
def convert_relay_readonly(attribute_name):
  p = property(
    lambda self:
      cg_to_py(getattr(self.node, attribute_name))
  )
  return p
  
def str_relay(attribute_name):
  p = property(
    lambda self:
      str(method_or_not(getattr(self.node, attribute_name))),
    lambda self, value:
      setattr(self.node, attribute_name, value)
  )
  return p
  
def no_op():
  '''Property that does nothing, used by Scene to masquerade as a regular node. '''
  p = property(
    lambda self:
      None,
    lambda self, value:
      None
  )
  return p
  
def color_prop(self, attribute, *value):
  if value:
    value = ui.parse_color(value[0])
    setattr(self.node, attribute, UIColor.color(red=value[0], green=value[1], blue=value[2], alpha=value[3]))
  else:
    color = getattr(self.node, attribute)()
    return (
      color.red,
      color.green,
      color.blue,
      color.alpha
    )
  
def color_relay(attribute_name):
  p = property(
    lambda self:
      color_prop(self, attribute_name),
    lambda self, value:
      color_prop(self, attribute_name, value)
  )
  return p
  
def physics_relay(attribute_name):
  '''Property creator for pass-through physics properties'''
  p = property(
    lambda self:
      method_or_not(getattr(self.node.physicsBody(), attribute_name)),
    lambda self, value:
      setattr(self.node.physicsBody(), attribute_name, value)
  )
  return p
  
def physics_relay_set(attribute_name):
  '''Property creator for pass-through physics properties'''
  set_name = 'set'+attribute_name[0].upper()+attribute_name[1:]+'_'
  p = property(
    lambda self:
      getattr(self.node.physicsBody(), attribute_name)(),
    lambda self, value:
      getattr(self.node.physicsBody(), 'set'+attribute_name[0].upper()+attribute_name[1:]+'_')(value)
  )
  return p
  
def boolean_relay(attribute_name):
  '''Property creator for pass-through physics properties'''
  get_name = 'is'+attribute_name[0].upper()+attribute_name[1:]
  set_name = 'set'+attribute_name[0].upper()+attribute_name[1:]+'_'
  p = property(
    lambda self:
      getattr(self.node, get_name)(),
    lambda self, value:
      getattr(self.node, set_name)(value)
  )
  return p
  
def physics_relay_readonly(attribute_name):
  '''Property creator for pass-through physics properties'''
  p = property(
    lambda self:
      getattr(self.node.physicsBody(), attribute_name)()
  )
  return p
  
def vector_physics_relay(attribute_name):
  p = property(
    lambda self:
      cg_to_py(method_or_not(getattr(self.node.physicsBody(), attribute_name))),
      #(getattr(self.node.physicsBody(), attribute_name)[0], 
      #getattr(self.node.physicsBody(), attribute_name)[1]),
    lambda self, value:
      setattr(self.node.physicsBody(), attribute_name, CGVector(*value))
  )
  return p
