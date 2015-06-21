import liblas
import sys
import struct

struct_fmt = 'fff' # float, float, float
struct_len = struct.calcsize(struct_fmt)
struct_pack = struct.Struct(struct_fmt).pack

tile = sys.argv[1]
f = liblas.file.File("/home/gt/Desktop/ahn/tiles/%s"%(tile), mode='r')
for p in f:
    floats = [p.x, p.y, p.z]
    s = struct_pack( *floats )
    sys.stdout.write( s )
    sys.stdout.flush()

