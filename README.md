# SCAN2STL
Generate 2D image projection as STL format 3D model.

---

# Quick start
## Docker
0. To build docker container, run the following for the first time.
```
$ docker compose build
```

1. Store your images in `img/` directory.

2. Start container.
```
$ docker compose up
```

3. Output stl file will be found in `stl/` directory.
