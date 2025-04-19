#include <Python.h>

typedef struct {
    PyObject_HEAD
    PyObject *ref;
} Class;

static int
init(Class *self, PyObject *args, PyObject *kwds) {
    PyObject *input = NULL;
    if (!PyArg_ParseTuple(args, "O", &input))
        return -1;
    Py_INCREF(input);
    self->ref = input;
    return 0;
}

static void
dealloc(Class *self) {
    Py_XDECREF(self->ref);
    Py_TYPE(self)->tp_free((PyObject *)self);
}

static PyObject *
get_ref(Class *self, void *closure) {
    Py_INCREF(self->ref);
    return self->ref;
}

static int
set_ref(Class *self, PyObject *value, void *closure) {
    if (value == self->ref) {
        return 0;
    }

    Py_XDECREF(self->ref);
    Py_INCREF(value);
    self->ref = value;
    return 0;
}

static PyGetSetDef Class_getsetters[] = {
    {"ref", (getter)get_ref, (setter)set_ref, "reference object", NULL},
    {NULL}
};

static PyTypeObject CTestClassType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "c_test.Class",
    .tp_basicsize = sizeof(Class),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_new = PyType_GenericNew,
    .tp_init = (initproc)init,
    .tp_dealloc = (destructor)dealloc,
    .tp_getset = Class_getsetters,
};

static PyModuleDef module = {
    PyModuleDef_HEAD_INIT,
    "c_test",
    "",
    -1,
    NULL, NULL, NULL, NULL, NULL
};

PyMODINIT_FUNC
PyInit_c_test(void) {
    if (PyType_Ready(&CTestClassType) < 0)
        return NULL;

    PyObject *m = PyModule_Create(&module);
    if (!m)
        return NULL;

    Py_INCREF(&CTestClassType);
    PyModule_AddObject(m, "Class", (PyObject *)&CTestClassType);
    return m;
}
