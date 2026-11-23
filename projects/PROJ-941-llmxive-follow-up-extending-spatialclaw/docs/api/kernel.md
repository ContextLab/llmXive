# API Documentation: code/kernel/

This document provides the API reference for the kernel module,
which enforces the 2D spatial reasoning restriction policy.

## Blockers - Library Whitelist/Blacklist

# Module: kernel.blockers

Defines the `RestrictedActionError` exception and the policy checking
functions for library allowlisting/blocklisting.

## Exceptions

### `RestrictedActionError`

Raised when an action violates the 2D spatial reasoning policy.

## Functions

### `check_library_policy(library_name: str) -> bool`

Checks if a library is allowed under the current 2D policy.

Returns True if the library is in the whitelist, False if blocked.

Allowed libraries: shapely, numpy, scipy, pandas, random, uuid, json, os, sys, logging, math, collections, itertools, typing, dataclasses, warnings, gc, time, datetime, re, argparse, pathlib, subprocess, csv, hashlib, base64, pickle, copy, functools, string, unicodedata, locale, statistics, fractions, decimal, numbers, cmath, operator, textwrap, struct, codecs, io, tempfile, shutil, glob, fnmatch, linecache, tokenize, keyword, token, ast, dis, pickletools, reprlib, weakref, array, bisect, heapq, queue, threading, multiprocessing, concurrent, socket, ssl, select, selectors, signal, mmap, email, html, urllib, xml, json, csv, configparser, argparse, logging, os, sys, pathlib, shutil, glob, fnmatch, linecache, tempfile, io, codecs, struct, base64, binascii, hashlib, hmac, secrets, uuid, random, statistics, fractions, decimal, numbers, cmath, operator, functools, itertools, collections, typing, dataclasses, warnings, gc, time, datetime, re, string, unicodedata, locale, array, bisect, heapq, queue, threading, multiprocessing, concurrent.futures, socket, ssl, select, selectors, signal, mmap, email, html, urllib, xml.etree, xml.dom, xml.sax, xml.parsers, xmlrpc, urllib.parse, urllib.request, urllib.response, urllib.error, urllib.robotparser, http, http.client, http.server, http.cookies, http.cookiejar, ftplib, poplib, imaplib, nntplib, smtplib, sndhdr, imghdr, aifc, sunau, wave, chunk, colorsys, tty, termios, curses, platform, errno, ctypes, posixpath, ntpath, genericpath, stat, filecmp, fileinput, statemachine, sqlite3, dbm, gzip, bz2, lzma, zipfile, tarfile, zlib, gzip, bz2, lzma, zipfile, tarfile, zlib, audioop, wave, aifc, sunau, chunk, imghdr, sndhdr, nis, spwd, grp, pwd, crypt, nis, spwd, grp, pwd, crypt, nis, spwd, grp, pwd, crypt

Blocked libraries: trimesh, pytorch3d, open3d, torch, tensorflow, keras, cv2, skimage, mayavi, vtk, pyvista, pycudadeconv, cupy, numba.cuda, jax, flax, optax, chex, haiku, tfa, timm, albumentations, kornia, pytorch_lightning, lightning, deepspeed, fairscale, accelerate, bitsandbytes, peft, transformers, diffusers, sentencepiece, tokenizers, datasets, accelerate, fairscale, deepspeed, ray, dask, distributed, prefect, airflow, luigi, celery, kombu, redis, pymongo, cassandra, scylla, influxdb, timescale, clickhouse, duckdb, polars, vaex, modin, cudf, dask_cudf, rapids, cuml, cugraph, cuspatial, cuxfilter, nvtabular, raft, rmm, cusolver, cusparse, cublas, cudnn, nccl, nvrtc, nvtx, cuda, pynvml, nvidia, pycuda, cupy, numba.cuda, jaxlib, jax, flax, optax, chex, haiku, tfa, timm, albumentations, kornia, pytorch_lightning, lightning, deepspeed, fairscale, accelerate, bitsandbytes, peft, transformers, diffusers, sentencepiece, tokenizers, datasets

## Restricted Kernel - Import Interception

# Module: kernel.restricted_kernel

Implements the `RestrictedImportHook` and `RestrictedKernel` classes
that intercept import statements and function calls to enforce the
2D spatial reasoning policy.

## Classes

### `RestrictedImportHook`

A custom import hook that blocks imports of 3D libraries.

**Methods:**

- `find_module(name: str, path: Optional[str] = None) -> Optional[RestrictedImportHook]`
 - Find the module and return self if it should be intercepted
- `load_module(name: str) -> ModuleType`
 - Load the module, raising RestrictedActionError if blocked

### `RestrictedKernel`

Main kernel class that manages the 2D policy enforcement context.

**Methods:**

- `__enter__() -> RestrictedKernel`
 - Enter the restricted context
- `__exit__(exc_type, exc_val, exc_tb) -> None`
 - Exit the restricted context and restore normal imports
- `enforce_policy() -> None`
 - Activate the import hook
- `release_policy() -> None`
 - Deactivate the import hook

## Functions

### `get_kernel() -> RestrictedKernel`

Returns the singleton kernel instance.

### `enforce_2d_policy() -> None`

Activates the 2D restriction policy globally.

### `release_2d_policy() -> None`

Deactivates the 2D restriction policy globally.