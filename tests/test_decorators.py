DECORATOR = """
        import asyncio
    
        from asyncio import get_running_loop
        from concurrent.futures.thread import ThreadPoolExecutor
        
        import pytest
        import decorator
    
    
        def sync_to_async(func):
            pool = ThreadPoolExecutor()
            
            async def wrapper(func, *args, **kwargs):
                loop = get_running_loop()
                return await loop.run_in_executor(pool, func, *args)
            dec = decorator.decorator(wrapper, func)
            return pytest.mark.decorated(dec)
    
    
"""


BAD_DECORATOR = """
        import pytest
        import decorator
        
        def bad_decorator(func):
            async def wrapper(func, *args, **kwargs):
                return await func(*args, **kwargs)
            dec = decorator.decorator(wrapper, func)
            return dec
            
            
"""


FIXTURE_X = """
        @pytest.fixture
        def x():
            return 0
            
            
"""

FIXTURE_Y = """
        @pytest.fixture
        def y(x):
            return x + 1


"""


def test_function_decorator_and_fixture(testdir):
    testdir.makeconftest("""""")

    testdir.makepyfile(
        DECORATOR + FIXTURE_X + """


        @pytest.mark.asyncio_cooperative
        @sync_to_async
        def test_a(x):
            assert x == 0
    """
    )

    result = testdir.runpytest()

    result.assert_outcomes(passed=1)


def test_function_decorator_parametrize(testdir):
    testdir.makeconftest("""""")

    testdir.makepyfile(
        DECORATOR + """

        @pytest.mark.parametrize(
            "y", [1, 2]
        )
        @pytest.mark.asyncio_cooperative
        @sync_to_async
        def test_a(y):
            assert y > 0
    """
    )

    result = testdir.runpytest()

    result.assert_outcomes(passed=2)


def test_function_decorator_fixtures_and_parametrize(testdir):
    testdir.makeconftest("""""")

    testdir.makepyfile(
        DECORATOR + FIXTURE_X + FIXTURE_Y + """
        @pytest.mark.parametrize(
            "param", [1, 2]
        )
        @pytest.mark.asyncio_cooperative
        @sync_to_async
        def test_a(x, y, param):
            x == 0
            assert y > x
            assert param > 0
    """
    )

    result = testdir.runpytest()

    result.assert_outcomes(passed=2)


def test_method_decorator_and_fixture(testdir):
    testdir.makeconftest("""""")

    testdir.makepyfile(
        DECORATOR + FIXTURE_X + """

        class Test:
            @pytest.mark.asyncio_cooperative
            @sync_to_async
            def test_a(self, x):
                assert x == 0
    """
    )

    result = testdir.runpytest()

    result.assert_outcomes(passed=1)


def test_method_decorator_fixtures_and_parametrize(testdir):
    testdir.makeconftest("""""")

    testdir.makepyfile(
        DECORATOR + FIXTURE_X + FIXTURE_Y + """
        class Test:
            @pytest.mark.parametrize(
                "param", [1, 2]
            )
            @pytest.mark.asyncio_cooperative
            @sync_to_async
            def test_a(self, x, y, param):
                x == 0
                assert y > x
                assert param > 0
    """
    )

    result = testdir.runpytest()

    result.assert_outcomes(passed=2)


def test_wrong_decorator(testdir):
    testdir.makeconftest("""""")

    testdir.makepyfile(
        BAD_DECORATOR + FIXTURE_X + """
        @pytest.mark.asyncio_cooperative
        @bad_decorator
        async def test(x):
            assert x == 0
    """
    )

    result = testdir.runpytest()

    result.assert_outcomes(failed=1)
    missed_x = False
    for line in result.outlines:
        if line == "E                           TypeError: missing a required argument: \'x\'":
            missed_x = True
            break
    assert missed_x
