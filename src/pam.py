#!/usr/bin/env python3
'''
exdm – The Extensible X Display Manager

Copyright © 2015  Mattias Andrée (maandree@member.fsf.org)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''


class PAM:
    '''
    Portable Arbitrary Map (PAM) file parser
    
    @variable  width:int     The width of image, in pixels
    @variable  height:int    The height of the image, in pixels
    @variable  depth:int     The number of channals, 1 for black and white or
                             greyscale, 3 for colour, plus 1 for alpha
    @variable  maxval:int    The maximum value a channel can have, the white point threshold
    @variable  tupltype:int  The channel configuration
    @variable  offset:int    The index of the first byte in the file for the first byte of the first pixel
    '''
    
    BLACKANDWHITE = 0
    '''
    :int  Value for `tupletype` when the image is black and white
          The bytes are: whitenames (note that it is not blackness as with P1 and P4)
          (note that it is bytes and not bits as with P4)
    '''
    
    GRAYSCALE = 1
    '''
    :int  Value for `tupletype` when the image is grey
          The words are: whiteness
    '''
    
    RGB = 2
    '''
    :int  Value for `tupletype` when the image is coloured
          The words are: redness, greenness, blueness
    '''
    
    BLACKANDWHITE_ALPHA = 3
    '''
    :int  Value for `tupletype` when the image is black and white with an alpha channel
          The bytes are: blackness (note that it is not blackness as with P1 and P4), transparency
    '''
    
    GRAYSCALE_ALPHA = 4
    '''
    :int  Value for `tupletype` when the image is grey with an alpha channel
          The words are: whiteness, transparency
    '''
    
    RGB_ALPHA = 5
    '''
    :int  Value for `tupletype` when the image is coloured with an alpha channel
          The words are: redness, greenness, blueness, transparency
    '''
    
    
    def __init__(self):
        '''
        Constructor
        '''
        self.width    = None
        self.height   = None
        self.depth    = None
        self.maxval   = None
        self.tupltype = None
    
    
    @staticmethod
    def parse(data : bytes) -> PAM:
        '''
        Parse an PAM-file
        
        @param   data:bytes  The file content
        @return  :PAM?       Metadata for the image, `None` on error (corrupt file)
        '''
        meta = PAM()
        meta.offset = 0
        ok = False
        
        TUPLTYPES = { 'BLACKANDWHITE'       : PAM.BLACKANDWHITE
                    , 'GRAYSCALE'           : PAM.GRAYSCALE
                    , 'RGB'                 : PAM.RGB
                    , 'BLACKANDWHITE_ALPHA' : PAM.BLACKANDWHITE_ALPHA
                    , 'GRAYSCALE_ALPHA'     : PAM.GRAYSCALE_ALPHA
                    , 'RGB_ALPHA'           : PAM.RGB_ALPHA
                    }
        
        buf = ''
        stage = 0
        try:
            for c in data:
                c = chr(c)
                meta.offset += 1
                if c == '\n':
                    buf = buf.strip()
                    if buf == 'P7':
                        if not stage == 0:
                            break
                        stage = 1
                    elif buf == 'ENDHDR':
                        ok = True
                        break
                    elif buf.startswith('WIDTH'):
                        if meta.width is not None: break
                        meta.width = int(buf[5:].strip())
                    elif buf.startswith('HEIGHT'):
                        if meta.height is not None: break
                        meta.height = int(buf[6:].strip())
                    elif buf.startswith('DEPTH'):
                        if meta.depth is not None: break
                        meta.depth = int(buf[5:].strip())
                    elif buf.startswith('MAXVAL'):
                        if meta.maxval is not None: break
                        meta.maxval = int(buf[6:].strip())
                    elif buf.startswith('TUPLTYPE'):
                        if meta.tupltype is not None: break
                        meta.tupltype = TUPLTYPES[buf[8:].strip()]
                else:
                    buf += c
        except:
            del meta
            return None
        
        if not ok:
            del meta
            return None
        
        if any([x is None for x in (meta.width, meta.height, meta.depth, meta.maxval, meta.tupltype)]):
            ok = False
        elif (meta.width < 1) or (meta.height < 1):     ok = False
        elif meta.tupltype == PAM.BLACKANDWHITE:        ok = (depth == 1) and (1 <= maxval <= 1)
        elif meta.tupltype == PAM.GRAYSCALE:            ok = (depth == 1) and (1 <= maxval <= 65535)
        elif meta.tupltype == PAM.RGB:                  ok = (depth == 3) and (1 <= maxval <= 65535)
        elif meta.tupltype == PAM.BLACKANDWHITE_ALPHA:  ok = (depth == 2) and (1 <= maxval <= 1)
        elif meta.tupltype == PAM.GRAYSCALE_ALPHA:      ok = (depth == 2) and (1 <= maxval <= 65535)
        elif meta.tupltype == PAM.RGB_ALPHA:            ok = (depth == 4) and (1 <= maxval <= 65535)
        if not ok:
            del meta
            return None
        return meta

