# iOS SpriteKit wrapper for Pythonista

If you are familiar with Pythonista scene module, many things will feel familiar. Look at Apple SpriteKit docs for more details.

## Supported nodes and attributes

### Node

All other nodes are inherited from Node and share its attributes. All writeable attributes can also be provided at initialization.

* children
* parent
* scale
* scale_x
* scale_y
* affected_by_gravity - boolean
* allows_rotation - boolean
* alpha
* anchor_point - default (0.5, 0.5)
* area - read only
* angular_damping - 0.0 to 1.0
* angular_velocity
* background_color = fill_color
* bbox - with children
* bullet_physics - boolean
* contact_bitmask
* density
* dynamic - boolean
* frame - this node only
* friction - 0.0 to 1.0
* hidden
* linear_damping - 0.0 to 1.0
* mass
* name
* physics_body - ObjC object
* position
* resting - boolean
* restitution - 0.0 to 1.0
* rotation
* size
* touch_enabled
* velocity
* z_position

### PathNode(path)

Argument: ui.Path

### PointsNode(points, smooth=False)

Arguments: list of points, if smooth is true, the line connecting the points will be a smooth spline

### BoxNode(size)

### CircleNode(radius)

### SpriteNode(image)

### CaneraNode
