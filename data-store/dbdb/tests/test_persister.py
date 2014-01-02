from StringIO import StringIO
import os

from nose.tools import eq_

from dbdb.persister import Persister


class TestPersister(object):

    def setup(self):
        self.f = StringIO()
        self.p = Persister(self.f)

    def _get_superblock_and_data(self, value):
        superblock = value[:Persister.SUPERBLOCK_SIZE]
        data = value[Persister.SUPERBLOCK_SIZE:]
        return superblock, data

    def test_init_ensures_superblock(self):
        EMPTY_SUPERBLOCK = ('\x00' * Persister.SUPERBLOCK_SIZE)
        self.f.seek(0, os.SEEK_END)
        value = self.f.getvalue()
        eq_(value, EMPTY_SUPERBLOCK)

    def test_write(self):
        self.p.write('ABCDE')
        value = self.f.getvalue()
        superblock, data = self._get_superblock_and_data(value)
        eq_(data, '\x00\x00\x00\x00\x00\x00\x00\x05ABCDE')

    def test_read(self):
        self.f.seek(Persister.SUPERBLOCK_SIZE)
        self.f.write('\x00\x00\x00\x00\x00\x00\x00\x0801234567')
        value = self.p.read(Persister.SUPERBLOCK_SIZE)
        eq_(value, '01234567')

    def test_commit_root_address(self):
        self.p.commit_root_address(257)
        root_bytes = self.f.getvalue()[:8]
        eq_(root_bytes, '\x00\x00\x00\x00\x00\x00\x01\x01')

    def test_get_root_address(self):
        self.f.seek(0)
        self.f.write('\x00\x00\x00\x00\x00\x00\x02\x02')
        root_address = self.p.get_root_address()
        eq_(root_address, 514)

    def test_workflow(self):
        a1 = self.p.write('one')
        a2 = self.p.write('two')
        self.p.commit_root_address(a2)
        a3 = self.p.write('three')
        eq_(self.p.get_root_address(), a2)
        a4 = self.p.write('four')
        self.p.commit_root_address(a4)
        eq_(self.p.read(a1), 'one')
        eq_(self.p.read(a2), 'two')
        eq_(self.p.read(a3), 'three')
        eq_(self.p.read(a4), 'four')
        eq_(self.p.get_root_address(), a4)
