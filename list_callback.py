def callback_method(func):
    def notify(self,*args,**kwargs):
        value = func(self,*args,**kwargs)
        self._callback()
        return value
    return notify

class NotifyList(list):
    extend = callback_method(list.extend)
    append = callback_method(list.append)
    remove = callback_method(list.remove)
    pop = callback_method(list.pop)
    __delitem__ = callback_method(list.__delitem__)
    __setitem__ = callback_method(list.__setitem__)
    __iadd__ = callback_method(list.__iadd__)
    __imul__ = callback_method(list.__imul__)

    def __getitem__(self,item):
        if isinstance(item,slice):
            return self.__class__(list.__getitem__(self,item))
        else:
            return list.__getitem__(self,item)

    def __init__(self,*args, callback=None):
        list.__init__(self,*args)
        self._callback = callback


if __name__ == '__main__':
    def cb():
        print ("Modify!")
  
    A = NotifyList(range(10), callback=cb)

    #register a callback
    #cbid = A.register_callback(cb)

    A.append('Foo')
    A += [1,2,3]
    A *= 3
    A[1:2] = [5]
    del A[1:2]

    A[5] = 'qux'
    print ("-"*80)

    print (A)
    print (type(A[1:3]))
    print (type(A[1:3:2]))
    print (type(A[5]))
