import ui
from objc_util import *
from objc_util import ObjCInstanceMethodProxy
from scene import Rect, Size, Vector2
import types


load_framework('SpriteKit')

SK_classes = [
  'SKView', 'SKScene', 'SKNode',
  'SKShapeNode', 'SKSpriteNode',
  'SKLabelNode',
  'SKEmitterNode',
  'SKPhysicsBody',
  'SKCameraNode', 'SKLightNode',
  'SKTexture',
  'SKEffectNode',
  'SKLightNode',
  'SKFieldNode', 'SKRegion',
  'SKConstraint', 'SKRange',
  'SKAction',
  'SKTextureAtlas',
  'SKWarpGeometryGrid',
  'SKPhysicsJointFixed',
  'SKPhysicsJointLimit',
  'SKPhysicsJointPin',
  'SKPhysicsJointSliding',
  'SKPhysicsJointSpring',
]

for class_name in SK_classes:
  globals()[class_name] = ObjCClass(class_name)


class Range:
  
  def __init__(self, range):
    self.range = range
    
  @classmethod
  def enable(cls, objc_range):
    methods = {
      'upper_limit': Range.upper_limit,
      'lower_limit': Range.lower_limit
    }
    for key in methods:
      setattr(objc_range, key, types.MethodType(methods[key], objc_range))
    return objc_range

  def upper_limit(self):
    return self.upperLimit()
    
  def lower_limit(self):
    return self.lowerLimit()
    
  @classmethod
  def zero(cls):
    return Range.enable(SKRange.rangeWithConstantValue_(0))
    
  @classmethod
  def constant(cls, value):
    return Range(SKRange.rangeWithConstantValue_(value))
    
  @classmethod
  def constant_o(cls, value):
    return Range.enable(SKRange.rangeWithConstantValue_(value))
    
  @classmethod
  def lower(cls, limit):
    return Range(SKRange.rangeWithLowerLimit_(limit))
    
  @classmethod
  def upper(cls, limit):
    return Range(SKRange.rangeWithUpperLimit_(limit))
    
  @classmethod
  def limits(cls, lower, upper):
    return Range(SKRange.rangeWithLowerLimit_upperLimit_(lower, upper))
    
  @classmethod
  def no_limits(cls):
    return Range(SKRange.rangeWithNoLimits())
    
  @classmethod
  def variance(cls, value, variance):
    return Range(SKRange.rangeWithValue_variance_(value, variance))


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

def method_or_not(value):
  return value() if type(value) == ObjCInstanceMethodProxy else value
  
def getter(source, attribute_name):
  is_name = 'is'+attribute_name[0].upper()+attribute_name[1:]
  if is_name in dir(source):
    attribute_name = is_name
  return method_or_not(getattr(source, attribute_name))
  
def setter(target, attribute_name, value):
  set_name = 'set'+attribute_name[0].upper()+attribute_name[1:]+'_'
  if set_name in dir(target):
    getattr(target, set_name)(value)
  else:
    setattr(target, attribute_name, value)

def prop(func):
  return property(func, func)

def node_relay(attribute_name):
  p = property(
    lambda self:
      getter(self.node, attribute_name),
    lambda self, value:
      setter(self.node, attribute_name, value)
  )
  return p
  
def node_convert(attribute_name):
  p = property(
    lambda self:
      cg_to_py(getter(self.node, attribute_name)),
    lambda self, value:
      setter(self.node, attribute_name, py_to_cg(value))
  )
  return p
  
def node_texture(attribute_name):
  p = property(
    lambda self:
      Texture(getter(self.node, attribute_name)),
    lambda self, value:
      setter(self.node, attribute_name, None if value is None else Texture(value).texture)
  )
  return p
  
def node_range(attribute_name):
  p = property(
    lambda self:
      Range(getter(self.node, attribute_name)),
    lambda self, value:
      setter(self.node, attribute_name, value.range)
  )
  return p
  
def node_convert_readonly(attribute_name):
  p = property(
    lambda self:
      cg_to_py(getter(self.node, attribute_name))
  )
  return p
  
def node_str(attribute_name):
  p = property(
    lambda self:
      str(method_or_not(getter(self.node, attribute_name))),
    lambda self, value:
      setter(self.node, attribute_name, value)
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
    setter(self.node, attribute, UIColor.color(red=value[0], green=value[1], blue=value[2], alpha=value[3]))
  else:
    color = getter(self.node, attribute)
    return (
      color.red(),
      color.green(),
      color.blue(),
      color.alpha()
    )
  
def node_color(attribute_name):
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
      method_or_not(getter(self.node.physicsBody(), attribute_name)),
    lambda self, value:
      setter(self.node.physicsBody(), attribute_name, value)
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
  
def physics_vector(attribute_name):
  p = property(
    lambda self:
      cg_to_py(getter(self.node.physicsBody(), attribute_name)),
      #(getattr(self.node.physicsBody(), attribute_name)[0], 
      #getattr(self.node.physicsBody(), attribute_name)[1]),
    lambda self, value:
      setter(self.node.physicsBody(), attribute_name, CGVector(*value))
  )
  return p
  
  
class Texture:
  
  def __init__(self, image_data):
    if type(image_data) == str:
      image_data = ui.Image(image_data)
    if type(image_data) == ui.Image:
      self.texture = SKTexture.textureWithImage_(ObjCInstance(image_data))
    elif type(image_data) == Texture:
      self.texture = image_data.texture
    else:
      self.texture = image_data
    
  @prop
  def size(self, *args):
    if args:
      value = args[0]
    else:
      return cg_to_py(self.texture.size())
    
  def crop(self, rect):
    return Texture(SKTexture.textureWithRect_inTexture_(py_to_cg(rect), self.texture))
    
  @classmethod
  def from_node(cls, node):
    return Texture(Node.textureFromNode_(node.node))
    
  def normal_map(self, smoothness=0.0, contrast=1.0):
    return self.texture.textureByGeneratingNormalMapWithSmoothness_contrast_(smoothness, contrast)
    
  @classmethod
  def noise_vector_map(self, size, smoothness=0.0):
    size=py_to_cg(size)
    return Texture(SKTexture.textureVectorNoiseWithSmoothness_size_(smoothness, size))
    
  def rounded_normal_map():
    '''Treats the R, G, and B components of each as the X, Y, and Z components of a surface normal vector.
    0 = -1.0, 127 = 0.0, 255 = 1.0
    '''
    pass
